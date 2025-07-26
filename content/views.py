from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from .models import (
    Lecture, Exam, Course,
    LectureAttendance, ExamAttendance,
    Question, Choice
)
from accounts.models import Student, Subscription

def home(request, grade, course_id):
    # جلب حالة التسجيل والطالب من الجلسة
    is_registered = request.session.get("is_registered", False)
    student = None
    if is_registered:
        student_id = request.session.get("student_id")
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            student = None

    # جلب الكورس والمحتوى
    course   = get_object_or_404(Course, id=course_id, grade=grade)
    lectures = Lecture.objects.filter(grade=grade, course=course)
    exams    = Exam.objects.filter(grade=grade, course=course)

    # تأكد من صلاحية الوصول: فردي أو جماعي
    if student:
        has_access = Subscription.objects.filter(
            is_active=True
        ).filter(
            Q(student=student) |
            Q(target_grade=student.grade)
        ).filter(
            courses=course
        ).exists()
        if not has_access:
            messages.error(request, "ليس لديك اشتراك للوصول إلى هذا الكورس.")
            return redirect('subscriptions')

        # تتبُّع اشتراك فردي
        student.courses.add(course)

    # تجميع المحتوى حسب الأسابيع
    WEEK_CHOICES = [
        ('week1', 'الأسبوع الأول'),
        ('week2', 'الأسبوع الثاني'),
        ('week3', 'الأسبوع الثالث'),
        ('week4', 'الأسبوع الرابع'),
    ]
    weeks_content = []
    for key, display in WEEK_CHOICES:
        lec_week  = [lec for lec in lectures if lec.week == key]
        exam_week = [ex  for ex  in exams    if ex.week == key]
        if lec_week or exam_week:
            weeks_content.append((display, lec_week, exam_week))

    return render(request, 'Test/home.html', {
        'lectures':      lectures,
        'exams':         exams,
        'grade':         grade,
        'course':        course,
        'weeks_content': weeks_content,
        'is_registered': is_registered,
    })


def exam_detail(request, exam_id):
    # تحقق من التسجيل
    is_registered = request.session.get("is_registered", False)
    if not is_registered:
        messages.error(request, "يجب عليك تسجيل الدخول لبدء الامتحان!")
        return redirect('accounts:login')

    exam = get_object_or_404(Exam, id=exam_id)
    student = None
    student_id = request.session.get("student_id")
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            student = None

    if student:
        # تحقق من الاشتراك الفردي أو الجماعي
        has_access = Subscription.objects.filter(
            is_active=True
        ).filter(
            Q(student=student) |
            Q(target_grade=student.grade)
        ).filter(
            courses=exam.course
        ).exists()
        if not has_access:
            messages.error(request, "ليس لديك اشتراك للوصول إلى هذا الامتحان.")
            return redirect("subscriptions")

        # سجل محاولة الطالب
        student.attempted_exams.add(exam)

        # ✅ تسجيل الحضور في جدول ExamAttendance
        ExamAttendance.objects.get_or_create(
            student=student,
            exam=exam,
            defaults={'status': 'present'}
        )

    questions = exam.questions.all()
    return render(request, "Test/exam_detail.html", {
        "exam":      exam,
        "questions": questions
    })



def lecture_detail(request, lecture_id):
    is_registered = request.session.get("is_registered", False)
    if not is_registered:
        messages.error(request, "يجب عليك تسجيل الدخول لمشاهدة المحاضرة!")
        return redirect('accounts:login')

    lecture = get_object_or_404(Lecture, id=lecture_id)
    student = None
    student_id = request.session.get("student_id")
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            student = None

    if student:
        has_access = Subscription.objects.filter(
            is_active=True
        ).filter(
            Q(student=student) |
            Q(target_grade=student.grade)
        ).filter(
            courses=lecture.course
        ).exists()
        if not has_access:
            messages.error(request, "ليس لديك اشتراك للوصول إلى هذه المحاضرة.")
            return redirect("subscriptions")

        # سجل مشاهدة الطالب للمحاضرة
        student.viewed_lectures.add(lecture)

        # ✅ تأكد من إنشاء أو تحديث حضور المحاضرة
        attendance, created = LectureAttendance.objects.get_or_create(
            student=student,
            lecture=lecture,
            defaults={"status": "present"}
        )
        if not created and attendance.status != 'present':
            attendance.status = 'present'
            attendance.save()

    return render(request, "Test/lecture_detail.html", {
        "lecture": lecture
    })




@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    student, created = Student.objects.get_or_create(user=request.user)

    if request.method == "POST":
        correct_answers = 0
        total_questions = exam.questions.count()
        student_answers = {}

        for question in exam.questions.all():
            key    = f"question{question.id}"
            answer = request.POST.get(key)

            if question.question_type == "mcq":
                choice = Choice.objects.filter(id=answer, question=question).first()
                if choice and choice.is_correct:
                    correct_answers += 1
                student_answers[question.id] = choice.text if choice else "لم يتم الإجابة"
            else:
                student_answers[question.id] = answer or "لم يتم الإجابة"

        score = round((correct_answers / total_questions) * 100, 2) if total_questions else 0

        return render(request, "Test/exam_feedback.html", {
            "exam":            exam,
            "student_answers": student_answers,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "score":           score,
        })

    return redirect("Test/exam_detail", exam_id=exam.id)


@login_required
def exam_analysis(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    analysis = []
    for q in exam.questions.all():
        total   = q.choices.count()
        correct = q.choices.filter(is_correct=True).count()
        analysis.append({
            "text":              q.text,
            "correct_count":     correct,
            "incorrect_count":   total - correct,
            "correct_percentage": round((correct / total) * 100, 2) if total else 0
        })

    return render(request, "Test/exam_analysis.html", {
        "exam":             exam,
        "question_analysis": analysis
    })


def complete_exam(request, exam_id):
    student = Student.objects.get(user=request.user)
    exam    = Exam.objects.get(id=exam_id)
    if exam not in student.attempted_exams.all():
        student.attempted_exams.add(exam)
        student.exams_completed = student.attempted_exams.count()
        student.total_exam_completions += 1
        student.save()
    return redirect("Test/exam_results", exam_id=exam.id)


def start_exam(request, exam_id):
    student = Student.objects.get(user=request.user)
    exam    = Exam.objects.get(id=exam_id)
    student.total_exam_views += 1
    student.save()
    return redirect("Test/exam_detail", exam_id=exam.id)


def watch_video(request, lecture_id):
    student = Student.objects.get(user=request.user)
    lecture = Lecture.objects.get(id=lecture_id)
    student.total_video_views += 1
    student.save()
    # سجل مشاهدة الحضور للمحاضرة
    LectureAttendance.objects.filter(
        student=student,
        lecture=lecture
    ).update(status='present')
    return redirect("Test/lecture_detail", lecture_id=lecture.id)


def subscriptions(request):
    return render(request, "Test/subscriptions.html")


def course_list(request, grade=None):
    courses = Course.objects.filter(grade=grade) if grade else Course.objects.all()
    return render(request, 'Test/courses.html', {'courses': courses})
