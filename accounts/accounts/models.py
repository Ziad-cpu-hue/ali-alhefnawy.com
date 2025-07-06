from django.db import models
from content.models import Course  # نموذج الكورسات الأساسي
from django.contrib.auth.models import User  
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password  
from content.models import Lecture, Exam  # استيراد المحاضرات والامتحانات

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)  # ربط الطالب بالمستخدم (يسمح بالقيم الفارغة مؤقتًا)
    first_name = models.CharField(max_length=100, verbose_name="الاسم الأول")
    last_name = models.CharField(max_length=100, verbose_name="الاسم الأخير")
    phone_number = models.CharField(max_length=15, verbose_name="رقم الهاتف")
    parent_phone_number = models.CharField(max_length=15, verbose_name="رقم هاتف ولي الأمر", null=True, blank=True)
    governorate = models.CharField(max_length=100, verbose_name="المحافظة")
    grade = models.CharField(
        max_length=50,
        verbose_name="الصف الدراسي",
        choices=[
            ('1', 'الصف الدراسي الأول'),
            ('2', 'الصف الدراسي الثاني'),
            ('3', 'الصف الدراسي الثالث'),
        ]
    )
    password = models.CharField(max_length=128, verbose_name="كلمة المرور", default='default_password')
    courses = models.ManyToManyField(Course, related_name='student_courses', verbose_name="الكورسات", blank=True)


    # العلاقات مع المحاضرات والامتحانات
    viewed_lectures = models.ManyToManyField('content.Lecture', related_name='students_who_watched', verbose_name="المحاضرات المشاهدة", blank=True)
    attempted_exams = models.ManyToManyField('content.Exam', related_name='students_who_attempted', verbose_name="الامتحانات المجربة", blank=True)

    videos_watched = models.PositiveIntegerField(default=0, verbose_name="عدد الفيديوهات المشاهدة")
    exams_completed = models.PositiveIntegerField(default=0, verbose_name="عدد الاختبارات المنهية")
    average_score = models.FloatField(default=0.0, verbose_name="متوسط النتائج")
    total_lecture_time = models.PositiveIntegerField(default=0, verbose_name="إجمالي مدة المحاضرات (بالدقائق)")
    total_video_views = models.PositiveIntegerField(default=0, verbose_name="إجمالي عدد مرات مشاهدة الفيديوهات")
    total_exam_views = models.PositiveIntegerField(default=0, verbose_name="إجمالي عدد مرات فتح الاختبارات")
    total_exam_completions = models.PositiveIntegerField(default=0, verbose_name="إجمالي عدد مرات إنهاء الاختبارات")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# تم حذف نموذج MonthlyCourse نهائيًا


# نموذج الاشتراكات المحدث
from django.db import models
from datetime import datetime
from accounts.models import Student
from content.models import Course

class Subscription(models.Model):
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name="subscriptions", 
        verbose_name="الطالب"
    )
    courses = models.ManyToManyField(
        Course, 
        related_name='students', 
        verbose_name="الكورسات", 
        blank=True
    )

    year = models.PositiveIntegerField(
        default=datetime.now().year, 
        verbose_name="السنة", 
        editable=False
    )
    is_active = models.BooleanField(
        default=False, 
        verbose_name="مفعل"
    )

    def activate_subscription(self):
        """تفعيل الاشتراك."""
        self.is_active = True
        self.save()

    def deactivate_subscription(self):
        """إلغاء تفعيل الاشتراك."""
        self.is_active = False
        self.save()

    def __str__(self):
        # عرض أسماء الكورسات المربوطة مفصولة بفاصلة
        course_names = ", ".join([course.title for course in self.courses.all()])
        return f"{self.student} - {course_names if course_names else 'No Course'} ({self.year})"

###############################################################################################

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class PaymentRequest(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    amount_required = models.DecimalField(max_digits=7, decimal_places=3, unique=True)

    sender_phone    = models.CharField(max_length=20, null=True, blank=True)   # رقم الهاتف الّذي أرسل الفلوس
    recipient_phone = models.CharField(max_length=20, null=True, blank=True)   # رقم الهاتف المستلم (رقم المنصة)
    txn_id          = models.CharField(max_length=50, null=True, blank=True)

    screenshot      = models.ImageField(upload_to='payments/')
    paid            = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)
    _phash          = models.CharField(max_length=16, null=True, blank=True)


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
