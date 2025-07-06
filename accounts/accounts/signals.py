

from django.db.models.signals import post_save
from django.dispatch import receiver
from content.models import Lecture, Exam
from django.contrib.auth.models import User
from .models import Student

@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    if created:
        Student.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_student_profile(sender, instance, **kwargs):
    instance.student.save()



from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from accounts.models import Student
from content.models import Lecture

@receiver(m2m_changed, sender=Student.viewed_lectures.through)
def update_watched_lectures(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        instance.videos_watched = instance.viewed_lectures.count()
        instance.total_lecture_time = sum(getattr(lecture, 'duration', 0) for lecture in instance.viewed_lectures.all())
        instance.save()



from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from accounts.models import Student

@receiver(m2m_changed, sender=Student.attempted_exams.through)
def update_average_score(sender, instance, action, **kwargs):
    # نفّذ التحديث بعد إضافة أو إزالة امتحان
    if action in ["post_add", "post_remove", "post_clear"]:
        completed_exams = instance.attempted_exams.all()
        if completed_exams:
            total_score = sum(
                sum(question.score for question in exam.questions.all())
                for exam in completed_exams
            )
            new_average = total_score / len(completed_exams)
        else:
            new_average = 0
        
        # فقط إذا تغير المتوسط نحدث القيمة لتجنب استدعاء save() متكرر
        if instance.average_score != new_average:
            instance.average_score = new_average
            instance.save(update_fields=["average_score"])



















"""
@receiver(post_save, sender=LectureContent)
def update_video_statistics(sender, instance, created, **kwargs):
    ""
    تحديث إحصائيات جميع الطلاب المشتركين في الكورس الذي تحتوي عليه المحاضرة.
    ""
    if created:
        students = instance.course.students.all()  # استخدام العلاقة العكسية من الكورس إلى الطلاب
        for student in students:
            student.videos_watched += 1
            student.total_video_views += 1
            student.total_lecture_time += instance.duration  # Assuming `duration` is in minutes
            student.save()

@receiver(post_save, sender=ExamContent)
def update_exam_statistics(sender, instance, created, **kwargs):
    ""
    تحديث إحصائيات جميع الطلاب عند إضافة امتحان جديد.
    ""
    if created:
        if hasattr(instance, "course") and hasattr(instance.course, "students"):
            students = instance.course.students.all()  # ✅ جلب الطلاب من الكورس المرتبط بالامتحان
        elif hasattr(instance, "students"):  # ✅ لو كان هناك علاقة مباشرة بـ students
            students = instance.students.all()
        else:
            print("⚠️ لا يوجد طلاب مرتبطون بهذا الامتحان.")
            return
        
        for student in students:
            student.exams_completed += 1
            student.total_exam_views += 1
            student.total_exam_completions += 1
            if hasattr(instance, "score"):  # ✅ التأكد أن الامتحان يحتوي على `score`
                student.average_score = (
                    (student.average_score * (student.exams_completed - 1)) + instance.score
                ) / student.exams_completed
            student.save()
"""