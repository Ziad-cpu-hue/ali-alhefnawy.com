from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Lecture, Exam, Course  # استخدام Course بدلاً من Card
from accounts.models import Student, Subscription

def home(request, grade, course_id):
    # استخدام حالة التسجيل من الجلسة بدلاً من request.user.is_authenticated
    is_registered = request.session.get("is_registered", False)
    student = None
    if is_registered:
        student_id = request.session.get("student_id")
        if student_id:
            try:
                student = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                student = None

    # جلب الكورس المحدد بناءً على الصف والمعرف
    course = get_object_or_404(Course, id=course_id, grade=grade)
    lectures = Lecture.objects.filter(grade=grade, course=course)
    exams = Exam.objects.filter(grade=grade, course=course)

    # تجميع المحتوى حسب الأسبوع
    WEEK_CHOICES = [
        ('week1', 'الأسبوع الأول'),
        ('week2', 'الأسبوع الثاني'),
        ('week3', 'الأسبوع الثالث'),
        ('week4', 'الأسبوع الرابع'),
    ]
    weeks_content = []
    for key, display in WEEK_CHOICES:
        lec_week = [lec for lec in lectures if lec.week == key]
        exam_week = [ex for ex in exams if ex.week == key]
        if lec_week or exam_week:
            weeks_content.append((display, lec_week, exam_week))

    if student:
        student.courses.add(course)

    context = {
        'lectures': lectures,
        'exams': exams,
        'grade': grade,
        'course': course,
        'weeks_content': weeks_content,
        'is_registered': is_registered,
    }
    return render(request, 'Test/home.html', context)

def exam_detail(request, exam_id):
    # التحقق من حالة التسجيل عبر الجلسة
    is_registered = request.session.get("is_registered", False)
    if not is_registered:
        messages.error(request, "يجب عليك تسجيل الدخول لبدء الامتحان!")
        return redirect("/login/")  # تأكد من أن هذا هو مسار تسجيل دخول الطلاب المناسب

    exam = get_object_or_404(Exam, id=exam_id)
    student = None
    student_id = request.session.get("student_id")
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            student = None

    if student:
        # تعديل هنا: استخدام 'courses' بدلاً من 'course'
        if not Subscription.objects.filter(student=student, courses=exam.course, is_active=True).exists():
            messages.error(request, "ليس لديك اشتراك للوصول إلى هذا الامتحان.")
            return redirect("subscriptions")  # تأكد أن "subscriptions" هو اسم مسار صفحة الاشتراكات
        # تسجيل أن الطالب دخل الامتحان
        student.attempted_exams.add(exam)

    questions = exam.questions.all()
    return render(request, "Test/exam_detail.html", {"exam": exam, "questions": questions})


def lecture_detail(request, lecture_id):
    # التحقق من حالة التسجيل عبر الجلسة
    is_registered = request.session.get("is_registered", False)
    if not is_registered:
        messages.error(request, "يجب عليك تسجيل الدخول لمشاهدة المحاضرة!")
        return redirect("/login/")  # تأكد من أن هذا هو مسار تسجيل دخول الطلاب المناسب

    lecture = get_object_or_404(Lecture, id=lecture_id)
    student = None
    student_id = request.session.get("student_id")
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            student = None

    if student:
        # هنا نقوم بالتحقق من وجود اشتراك نشط للطالب مع الكورس الخاص بالمحاضرة.
        # لاحظ أننا نستخدم الحقل "courses" في نموذج Subscription كما هو موجود.
        if not Subscription.objects.filter(student=student, courses=lecture.course, is_active=True).exists():
            messages.error(request, "ليس لديك اشتراك للوصول إلى هذه المحاضرة.")
            return redirect("subscriptions")  # تأكد من أن "subscriptions" هو مسار صفحة الاشتراكات
        student.viewed_lectures.add(lecture)

    return render(request, "Test/lecture_detail.html", {"lecture": lecture})




#""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Exam, Question, Choice
from accounts.models import Student

@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    student, created = Student.objects.get_or_create(user=request.user)

    if request.method == "POST":
        correct_answers = 0
        total_questions = exam.questions.count()
        student_answers = {}

        for question in exam.questions.all():
            question_key = f"question{question.id}"
            answer = request.POST.get(question_key)

            if question.question_type == "mcq":
                selected_choice = Choice.objects.filter(id=answer, question=question).first()
                if selected_choice and selected_choice.is_correct:
                    correct_answers += 1
                student_answers[question.id] = selected_choice.text if selected_choice else "لم يتم الإجابة"

            elif question.question_type == "essay":
                student_answers[question.id] = answer if answer else "لم يتم الإجابة"

        score = round((correct_answers / total_questions) * 100, 2) if total_questions > 0 else 0

        return render(request, "Test/exam_feedback.html", {
            "exam": exam,
            "student_answers": student_answers,  # تمرير القاموس مباشرة للقالب
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "score": score,
        })
    
    return redirect("Test/exam_detail", exam_id=exam.id)



@login_required
def exam_analysis(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    question_analysis = []
    for question in exam.questions.all():
        total_answers = question.choices.count()
        correct_count = question.choices.filter(is_correct=True).count()
        incorrect_count = total_answers - correct_count

        question_analysis.append({
            "text": question.text,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "correct_percentage": round((correct_count / total_answers) * 100, 2) if total_answers > 0 else 0
        })

    return render(request, "Test/exam_analysis.html", {
        "exam": exam,
        "question_analysis": question_analysis
    })
#""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""



from content.models import Exam
from accounts.models import Student

def complete_exam(request, exam_id):
    student = Student.objects.get(user=request.user)
    exam = Exam.objects.get(id=exam_id)

    if exam not in student.attempted_exams.all():  # ✅ إذا لم يكن الطالب قد أنهى هذا الاختبار من قبل
        student.attempted_exams.add(exam)
        student.exams_completed = student.attempted_exams.count()
        student.total_exam_completions += 1  # ✅ عدد المرات التي أنهى فيها الامتحانات
        student.save()
    
    return redirect("Test/exam_results", exam_id=exam.id)




def start_exam(request, exam_id):
    student = Student.objects.get(user=request.user)
    exam = Exam.objects.get(id=exam_id)

    student.total_exam_views += 1  # ✅ زيادة عدد المرات التي فتح فيها الطالب الامتحانات
    student.save()

    return redirect("Test/exam_detail", exam_id=exam.id)



def watch_video(request, lecture_id):
    student = Student.objects.get(user=request.user)
    lecture = Lecture.objects.get(id=lecture_id)

    student.total_video_views += 1  # ✅ زيادة عدد مرات مشاهدة الفيديوهات
    student.save()

    return redirect("Test/lecture_detail", lecture_id=lecture.id)


def subscriptions(request):
    return render(request, "Test/subscriptions.html")  # غير اسم القالب حسب الحاجة

#""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""



from django.shortcuts import render
from .models import Course

def course_list(request, grade=None):
    if grade:
        courses = Course.objects.filter(grade=grade)
    else:
        courses = Course.objects.all()
    return render(request, 'Test/courses.html', {'courses': courses})

#""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
