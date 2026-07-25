# accounts/signals.py

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from content.models import Lecture, Exam
from .models import Student


# ─── إنشاء ملف Student عند إنشاء User جديد ─────────────────────────────────
@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    if created:
        Student.objects.create(user=instance)


# ─── حفظ ملف Student المرتبط عند كل حفظ لـ User (مع اعتراض الخطأ إذا لم يكن موجوداً) ────
@receiver(post_save, sender=User)
def save_student_profile(sender, instance, **kwargs):
    try:
        instance.student.save()
    except ObjectDoesNotExist:
        # إذا لم يكن للمستخدم Student مرتبط بعد، نتجاهل الخطأ
        pass


# ─── تحديث إحصائيات المشاهدة عند تغيّر علاقة viewed_lectures ───────────────────────────
@receiver(m2m_changed, sender=Student.viewed_lectures.through)
def update_watched_lectures(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        instance.videos_watched = instance.viewed_lectures.count()
        instance.total_lecture_time = sum(
            getattr(lecture, 'duration', 0)
            for lecture in instance.viewed_lectures.all()
        )
        instance.save()


# ─── تحديث متوسط الدرجة عند تغيّر علاقة attempted_exams ────────────────────────────────
@receiver(m2m_changed, sender=Student.attempted_exams.through)
def update_average_score(sender, instance, action, **kwargs):
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

        if instance.average_score != new_average:
            instance.average_score = new_average
            instance.save(update_fields=["average_score"])
