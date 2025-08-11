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
# الآن Subscription يأتي بعد Student، فلا حاجة لاستيراد Student
GRADE_CHOICES = [
    ('1', 'الصف الدراسي الأول الثانوي'),
    ('2', 'الصف الدراسي الثاني الثانوي'),
    ('3', 'الصف الدراسي الثالث الثانوي'),
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
