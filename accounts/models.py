from django.db import models
from django.core.exceptions import ValidationError
from content.models import Course
from django.contrib.auth.models import User
from datetime import datetime
import re

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name="الاسم الأول")
    last_name = models.CharField(max_length=100, verbose_name="الاسم الأخير")
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="رقم الهاتف")
    parent_phone_number = models.CharField(max_length=15, unique=True, verbose_name="رقم هاتف ولي الأمر", null=True, blank=True)
    governorate = models.CharField(max_length=100, verbose_name="المحافظة")
    grade = models.CharField(
        max_length=50,
        verbose_name="الصف الدراسي",
        choices=[
            ('1', 'الصف الأول الثانوي'),
            ('2', 'الصف الثاني الثانوي'),
            ('3', 'الصف الثالث الثانوي'),
            ('4', 'أولى إعدادي'),
            ('5', 'تانية إعدادي'),
            ('6', 'تالته إعدادي'),
        ]
    )
    password = models.CharField(max_length=128, verbose_name="كلمة المرور", default='default_password')
    courses = models.ManyToManyField(Course, related_name='student_courses', verbose_name="الكورسات", blank=True)

    # ✅ حقل الصورة الشخصية
    avatar = models.ImageField(upload_to="avatars/%Y/%m/%d/", verbose_name="الصورة الشخصية", null=True, blank=True)

    def normalize_phone(self, phone):
        """تحويل الرقم إلى أرقام فقط (بدون مسافات أو علامات)"""
        return re.sub(r'\D', '', phone or '')

    def clean(self):
        """ تحقق من عدم التكرار + عدم تساوي رقم الطالب مع رقم ولي الأمر """
        # التحقق من phone_number
        if self.phone_number:
            qs = Student.objects.filter(phone_number=self.phone_number)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'phone_number': 'رقم الهاتف مستخدم بالفعل في النظام.'})

        # التحقق من parent_phone_number (لو موجود)
        if self.parent_phone_number:
            qs2 = Student.objects.filter(parent_phone_number=self.parent_phone_number)
            if self.pk:
                qs2 = qs2.exclude(pk=self.pk)
            if qs2.exists():
                raise ValidationError({'parent_phone_number': 'رقم ولي الأمر مستخدم بالفعل في النظام.'})

        # منع تساوي رقم الطالب مع رقم ولي الأمر
        phone = self.normalize_phone(self.phone_number)
        parent_phone = self.normalize_phone(self.parent_phone_number)
        if phone and parent_phone and phone == parent_phone:
            raise ValidationError("رقم الهاتف لا يمكن أن يكون نفس رقم هاتف ولي الأمر.")

        super().clean()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"





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
# الآن Subscription يأتي بعد Student، فلا حاجة لاستيراد Student
GRADE_CHOICES = [
    ('1', 'الصف الدراسي الأول الثانوي'),
    ('2', 'الصف الدراسي الثاني الثانوي'),
    ('3', 'الصف الدراسي الثالث الثانوي'),
    ('4', 'أولى إعدادي'),
    ('5', 'تانية إعدادي'),
    ('6', 'تالته إعدادي'),
]


class Subscription(models.Model):
    student = models.ForeignKey(
        Student,  # هنا نستخدم Student مباشرة
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="الطالب",
        null=True,
        blank=True
    )
    target_grade = models.CharField(
        max_length=1,
        choices=GRADE_CHOICES,
        verbose_name="صف دراسي مستهدف",
        null=True,
        blank=True,
        help_text="إذا ضبطت هذا الحقل، سيطبق الاشتراك على جميع طلبة هذا الصف الدراسي"
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

    def clean(self):
        super().clean()
        if bool(self.student) == bool(self.target_grade):
            raise ValidationError(
                "يجب تحديد طالب واحد أو صف دراسي مستهدف واحد فقط، لا الاثنين أو لا شيء."
            )

    def activate_subscription(self):
        self.is_active = True
        self.save()

    def deactivate_subscription(self):
        self.is_active = False
        self.save()

    def __str__(self):
        ref = self.student if self.student else dict(GRADE_CHOICES).get(self.target_grade, 'غير محدد')
        course_names = ", ".join([c.title for c in self.courses.all()])
        return f"{ref} – {course_names or 'No Course'} ({self.year})"

#################################################################

# ===== سجل نشاط الطالب (Activity Log) =====
class ActivityLog(models.Model):
    ACTIVITY_TYPES = [
        ('lecture_view', 'فتح صفحة المحاضرة'),
        ('lecture_progress', 'تقدّم مشاهدة المحاضرة'),
        ('lecture_present', 'اكتمل مشاهدة المحاضرة (حاضر)'),
        ('exam_started', 'بدء امتحان'),
        ('exam_submitted', 'تم إرسال إجابات الامتحان'),
        ('exam_completed', 'اكتمل الامتحان'),
        ('login', 'تسجيل دخول'),
        ('logout', 'تسجيل خروج'),
        ('other', 'نشاط آخر'),
    ]

    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name="الطالب"
    )
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES, verbose_name="نوع النشاط")
    lecture = models.ForeignKey('content.Lecture', null=True, blank=True, on_delete=models.CASCADE, verbose_name="المحاضرة")
    exam = models.ForeignKey('content.Exam', null=True, blank=True, on_delete=models.CASCADE, verbose_name="الامتحان")
    # تفاصيل مرنة (مثلاً: {"watched_seconds": 120, "lecture_duration": 300})
    details = models.JSONField(null=True, blank=True, verbose_name="تفاصيل")
    # بعض النشاطات قد تحمل درجة مئوية أو نتيجة نهائية
    score = models.FloatField(null=True, blank=True, verbose_name="الدرجة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="الوقت")

    class Meta:
        verbose_name = "سجل نشاط"
        verbose_name_plural = "سجلات النشاط"
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.student} — {self.get_activity_type_display()} @ {self.created_at:%Y-%m-%d %H:%M}"






