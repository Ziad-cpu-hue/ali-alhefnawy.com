from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
from django.apps import apps
from .models import Lecture, Exam, LectureAttendance, ExamAttendance

@receiver(post_save, sender=Lecture)
def init_lecture_attendance(sender, instance, created, **kwargs):
    if not created or not instance.course:
        return

    Subscription = apps.get_model('accounts', 'Subscription')
    Student = apps.get_model('accounts', 'Student')

    # إحضار الاشتراكات النشطة المرتبطة بالكورس
    subs = Subscription.objects.filter(
        is_active=True,
        courses=instance.course
    ).filter(
        Q(student__isnull=False) |
        Q(student__isnull=True, target_grade=instance.grade)
    )

    # إنشاء سجلات الحضور
    for sub in subs:
        if sub.student:
            # اشتراك مباشر لطالب محدد
            LectureAttendance.objects.create(student=sub.student, lecture=instance, status='absent')
        else:
            # اشتراك بالصف بالكامل
            for st in Student.objects.filter(grade=sub.target_grade):
                LectureAttendance.objects.create(student=st, lecture=instance, status='absent')


@receiver(post_save, sender=Exam)
def init_exam_attendance(sender, instance, created, **kwargs):
    if not created or not instance.course:
        return

    Subscription = apps.get_model('accounts', 'Subscription')
    Student = apps.get_model('accounts', 'Student')

    # إحضار الاشتراكات النشطة المرتبطة بالكورس
    subs = Subscription.objects.filter(
        is_active=True,
        courses=instance.course
    ).filter(
        Q(student__isnull=False) |
        Q(student__isnull=True, target_grade=instance.grade)
    )

    # إنشاء سجلات الحضور
    for sub in subs:
        if sub.student:
            # اشتراك مباشر لطالب محدد
            ExamAttendance.objects.create(student=sub.student, exam=instance, status='absent')
        else:
            # اشتراك بالصف بالكامل
            for st in Student.objects.filter(grade=sub.target_grade):
                ExamAttendance.objects.create(student=st, exam=instance, status='absent')
