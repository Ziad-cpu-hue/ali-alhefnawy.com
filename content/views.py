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

        # ✅ تسجيل الحضور في جدول ExamAttendance (كما كان)
        attendance, created = ExamAttendance.objects.get_or_create(
            student=student,
            exam=exam,
            defaults={'status': 'present'}
        )

        # محاولة تسجيل نشاط فتح الامتحان في ActivityLog (آمن)
        try:
            from django.apps import apps
            ActivityLog = apps.get_model('accounts', 'ActivityLog')
            ActivityLog.objects.create(
                student=student,
                activity_type='exam_started',
                exam=exam,
                details={
                    "note": "فتح صفحة الامتحان",
                    "attendance_created": bool(created),
                    "attendance_status": getattr(attendance, "status", None),
                    "answered_count": getattr(attendance, "answered_count", None),
                    "total_questions": getattr(attendance, "total_questions", None),
                }
            )
        except Exception:
            # لا نرمي أي خطأ لأننا لا نريد أن نكسر الوظيفة الأساسية إذا فشل سجل النشاط
            pass

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

        # نحتفظ بعلم إذا تغيّرت الحالة (تم إنشاؤه الآن أو تم تحويله إلى present)
        status_changed = False
        if created:
            status_changed = True
        else:
            if attendance.status != 'present':
                attendance.status = 'present'
                attendance.save()
                status_changed = True

        # محاولة تسجيل النشاط في ActivityLog (آمنة: لن تكسر الوظائف الأساسية إذا لم يكن الموديل موجود)
        try:
            from django.apps import apps
            ActivityLog = apps.get_model('accounts', 'ActivityLog')
            # سجل فتح المحاضرة
            ActivityLog.objects.create(
                student=student,
                activity_type='lecture_view',
                lecture=lecture,
                details={
                    "note": "فتح صفحة المحاضرة",
                    "lecture_duration": getattr(lecture, 'duration_seconds', 0)
                }
            )
            # إذا تم إنشاء حضور أو تغيّرت الحالة إلى present فسجل ذلك أيضاً
            if status_changed:
                ActivityLog.objects.create(
                    student=student,
                    activity_type='lecture_present',
                    lecture=lecture,
                    details={
                        "watched_seconds": getattr(attendance, 'watched_seconds', 0),
                        "lecture_duration": getattr(attendance, 'lecture_duration', getattr(lecture, 'duration_seconds', 0)),
                        "note": "حالة الحضور أصبحت حاضر (>=70%) أو تم إنشاء سجل الحضور"
                    }
                )
        except Exception:
            # لا نفشل الدالة الأساسية إذا فشل تسجيل النشاط لأي سبب (مثل غياب الموديل)
            pass

    return render(request, "Test/lecture_detail.html", {
        "lecture": lecture
    })





from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Exam, Choice, ExamAttendance
from accounts.models import Student

@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # 1. جلب الطالب من الجلسة (كما عند lecture_detail و exam_detail)
    student_id = request.session.get("student_id")
    if not student_id:
        # إذا لم يوجد طالب في الجلسة، نعيد للتسجيل
        return redirect('accounts:login')
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        total_questions = exam.questions.count()
        answered = 0
        correct_answers = 0
        student_answers = {}

        # 2. حساب عدد الإجابات وعدد الصحيحة
        for question in exam.questions.all():
            key = f"question{question.id}"
            answer = request.POST.get(key)
            if answer:
                answered += 1

            if question.question_type == "mcq":
                choice = Choice.objects.filter(id=answer, question=question).first()
                if choice and choice.is_correct:
                    correct_answers += 1
                student_answers[question.id] = choice.text if choice else "لم يتم الإجابة"
            else:
                student_answers[question.id] = answer or "لم يتم الإجابة"

        # 3. نسبة الدرجة النهائية (كما كان)
        score = round((correct_answers / total_questions) * 100, 2) if total_questions else 0

        # 4. تحديث سجل الحضور في ExamAttendance
        attendance, created = ExamAttendance.objects.get_or_create(
            student=student,
            exam=exam,
            defaults={"total_questions": total_questions, "answered_count": 0}
        )

        # حفظ الحالة السابقة للمقارنة لاحقاً
        prev_status = getattr(attendance, "status", "absent")

        # حدِّث القيم دوماً
        attendance.answered_count  = answered
        attendance.total_questions = total_questions
        attendance.save()  # داخلياً يشغّل update_status() في الموديل

        # ===== سجل النشاط في ActivityLog (آمن) =====
        try:
            from django.apps import apps
            ActivityLog = apps.get_model('accounts', 'ActivityLog')

            # سجل إرسال الامتحان مع التفاصيل والدرجة
            ActivityLog.objects.create(
                student=student,
                activity_type='exam_submitted',
                exam=exam,
                score=score,
                details={
                    "answered": answered,
                    "correct_answers": correct_answers,
                    "total_questions": total_questions,
                    "attendance_created": bool(created),
                    "attendance_prev_status": prev_status,
                    "attendance_status": getattr(attendance, "status", None)
                }
            )

            # إذا تغيّرت الحالة إلى present فسجل اكتمال الامتحان
            if getattr(attendance, "status", None) == 'present' and prev_status != 'present':
                ActivityLog.objects.create(
                    student=student,
                    activity_type='exam_completed',
                    exam=exam,
                    details={
                        "note": "أكمل الامتحان (>=70% من الأسئلة أو شرط الحضور تحقق)",
                        "answered": answered,
                        "total_questions": total_questions,
                        "score": score
                    }
                )
        except Exception:
            # لا نريد أن نفشل عملية submit الأساسية لمجرد فشل تسجيل النشاط
            pass

        return render(request, "Test/exam_feedback.html", {
            "exam":             exam,
            "student_answers":  student_answers,
            "correct_answers":  correct_answers,
            "total_questions":  total_questions,
            "score":            score,
            "attendance_status": attendance.status,
        })

    return redirect("Test:exam_detail", exam_id=exam.id)




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

    # حالات سابقة للاطلاع على التغيير
    prev_attempted = student.attempted_exams.filter(id=exam.id).exists()
    prev_exams_completed = getattr(student, "exams_completed", 0)
    prev_total_exam_completions = getattr(student, "total_exam_completions", 0)

    if exam not in student.attempted_exams.all():
        student.attempted_exams.add(exam)
        student.exams_completed = student.attempted_exams.count()
        student.total_exam_completions += 1
        student.save()

    # تسجيل النشاط في ActivityLog بشكل آمن (لا يكسر الوظيفة إذا فشل التسجيل)
    try:
        from django.apps import apps
        ActivityLog = apps.get_model('accounts', 'ActivityLog')
        # حاول الحصول على سجل الحضور إن وُجد لإضافة معلومات إضافية
        try:
            attendance = ExamAttendance.objects.filter(student=student, exam=exam).first()
            attendance_info = {
                "attendance_status": getattr(attendance, "status", None),
                "answered_count": getattr(attendance, "answered_count", None),
                "total_questions": getattr(attendance, "total_questions", None),
            } if attendance else {}
        except Exception:
            attendance_info = {}

        ActivityLog.objects.create(
            student=student,
            activity_type='exam_completed',
            exam=exam,
            details={
                "prev_attempted": prev_attempted,
                "prev_exams_completed": prev_exams_completed,
                "prev_total_exam_completions": prev_total_exam_completions,
                "now_exams_completed": getattr(student, "exams_completed", None),
                "now_total_exam_completions": getattr(student, "total_exam_completions", None),
                **attendance_info
            }
        )
    except Exception:
        # لا نفشل عملية complete_exam الأساسية لمجرد فشل تسجيل النشاط
        pass

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



# content/views.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

@login_required
@require_POST
def update_watch_progress(request, lecture_id):
    from django.shortcuts import get_object_or_404
    from django.apps import apps

    # جلب الطالب من ال-session مع تعامل آمن
    try:
        student = Student.objects.get(id=request.session.get("student_id"))
    except (Student.DoesNotExist, TypeError):
        return JsonResponse({"error": "Student not found in session."}, status=403)

    lecture = get_object_or_404(Lecture, id=lecture_id)

    # قراءة القيم بأمان
    try:
        seconds = int(request.POST.get("watched_seconds", 0))
    except (ValueError, TypeError):
        seconds = 0
    try:
        duration = int(request.POST.get("lecture_duration", 0))
    except (ValueError, TypeError):
        duration = 0

    attendance, created = LectureAttendance.objects.get_or_create(
        student=student,
        lecture=lecture,
        defaults={"watched_seconds": 0, "lecture_duration": duration}
    )

    # حفظ الحالة السابقة للمقارنة لاحقاً
    prev_status = getattr(attendance, "status", "absent")
    prev_watched = getattr(attendance, "watched_seconds", 0)

    # حدِّث طول المحاضرة لو تغيّر أو كان صفر
    if duration and attendance.lecture_duration != duration:
        attendance.lecture_duration = duration

    # زيِّد الثواني المشاهدة (لا تتجاوز مدة المحاضرة)
    attendance.watched_seconds = min(
        attendance.watched_seconds + seconds,
        attendance.lecture_duration
    )
    attendance.save()  # داخلياً يتم update_status()

    # حاول تسجيل النشاط في ActivityLog (آمن: لن يفشل لو الموديل غير موجود)
    try:
        ActivityLog = apps.get_model('accounts', 'ActivityLog')

        # سجل تقدّم المشاهدة عند وجود تغيير فعلي في الثواني أو عند الإنشاء الأولي
        if seconds > 0 or created:
            ActivityLog.objects.create(
                student=student,
                activity_type='lecture_progress',
                lecture=lecture,
                details={
                    "delta_seconds": seconds,
                    "watched_seconds": attendance.watched_seconds,
                    "lecture_duration": attendance.lecture_duration,
                    "prev_watched_seconds": prev_watched,
                    "prev_status": prev_status,
                    "status": attendance.status,
                }
            )

        # إذا تغيّرت الحالة إلى 'present' فسجّل حدث اكتمال الحضور
        if attendance.status == 'present' and prev_status != 'present':
            ActivityLog.objects.create(
                student=student,
                activity_type='lecture_present',
                lecture=lecture,
                details={
                    "watched_seconds": attendance.watched_seconds,
                    "lecture_duration": attendance.lecture_duration,
                    "note": "وصل 70% أو أكثر من المحاضرة"
                }
            )
    except Exception:
        # لا نريد أن نفشل تحديث المشاهدة الأساسي لمجرد فشل تسجيل النشاط
        pass

    return JsonResponse({
        "watched_seconds": attendance.watched_seconds,
        "lecture_duration": attendance.lecture_duration,
        "status": attendance.status
    })
