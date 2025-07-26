from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Lecture
from accounts.models import Subscription  # تأكد أن هذا هو المسار الصحيح للنموذج

@receiver(post_save, sender=Lecture)
def initialize_attendance(sender, instance, created, **kwargs):
    if not created or not instance.course:
        return

    def populate_attendance():
        # نأتي بجميع اشتراكات الكورس الشهري لهذا الطالب
        subscriptions = Subscription.objects.filter(courses=instance.course)
        student_ids = list(subscriptions.values_list('student_id', flat=True))

        instance.attendance = {
            'absent': student_ids,
            'present': []
        }
        Lecture.objects.filter(pk=instance.pk).update(attendance=instance.attendance)

    transaction.on_commit(populate_attendance)
#######################################################################################





from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
from django.apps import apps
from .models import Lecture, Exam, LectureAttendance, ExamAttendance

@receiver(post_save, sender=Lecture)
def init_lecture_attendance(sender, instance, created, **kwargs):
    if not created:
        return
    Subscription = apps.get_model('accounts', 'Subscription')
    Student      = apps.get_model('accounts', 'Student')

    subs = Subscription.objects.filter(
        is_active=True,
        courses=instance.course
    ).filter(
        Q(student__isnull=False) |
        Q(student__isnull=True, target_grade=instance.grade)
    )
    for sub in subs:
        if sub.student:
            LectureAttendance.objects.create(student=sub.student, lecture=instance, status='absent')
        else:
            for st in Student.objects.filter(grade=sub.target_grade):
                LectureAttendance.objects.create(student=st, lecture=instance, status='absent')


@receiver(post_save, sender=Exam)
def init_exam_attendance(sender, instance, created, **kwargs):
    if not created:
        return
    Subscription = apps.get_model('accounts', 'Subscription')
    Student      = apps.get_model('accounts', 'Student')

    subs = Subscription.objects.filter(
        is_active=True,
        courses=instance.course
    ).filter(
        Q(student__isnull=False) |
        Q(student__isnull=True, target_grade=instance.grade)
    )
    for sub in subs:
        if sub.student:
            ExamAttendance.objects.create(student=sub.student, exam=instance, status='absent')
        else:
            for st in Student.objects.filter(grade=sub.target_grade):
                ExamAttendance.objects.create(student=st, exam=instance, status='absent')
