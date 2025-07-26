from django.db import models

# ─── خيارات الصف الدراسي والأسابيع وأنواع الأسئلة ───────────────────────
GRADE_CHOICES = [
    ('first',  'الصف الأول'),
    ('second', 'الصف الثاني'),
    ('third',  'الصف الثالث'),
]

WEEK_CHOICES = [
    ('week1', 'الأسبوع الأول'),
    ('week2', 'الأسبوع الثاني'),
    ('week3', 'الأسبوع الثالث'),
    ('week4', 'الأسبوع الرابع'),
]

QUESTION_TYPE_CHOICES = [
    ('mcq',   'اختياري'),
    ('essay', 'مقالي'),
]

# ─── نموذج الكورس ────────────────────────────────────────────────────────
class Course(models.Model):
    title       = models.CharField(max_length=255, verbose_name="عنوان الكورس")
    description = models.TextField(verbose_name="الوصف")
    image       = models.ImageField(upload_to='course_images/', verbose_name="الصورة")
    price       = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    grade       = models.CharField(max_length=10, choices=GRADE_CHOICES, verbose_name="الصف الدراسي", default='first')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at  = models.DateTimeField(auto_now=True,      verbose_name="آخر تحديث")

    class Meta:
        verbose_name        = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return f"{self.title} - {self.get_grade_display()}"


# ─── نموذج المحاضرة ──────────────────────────────────────────────────────
# content/models.py

from django.db import models

class Lecture(models.Model):
    # الحقول الحالية...
    title          = models.CharField(max_length=255, verbose_name="عنوان المحاضرة")
    description    = models.TextField(verbose_name="الوصف", null=True, blank=True)
    video          = models.FileField(upload_to="videos/", verbose_name="ملف الفيديو", blank=True, null=True)
    youtube_iframe = models.TextField(verbose_name="كود تضمين فيديو YouTube", blank=True, null=True)
    grade          = models.CharField(max_length=10, choices=GRADE_CHOICES, verbose_name="الصف الدراسي", null=True, blank=True)
    course         = models.ForeignKey("Course", on_delete=models.CASCADE, verbose_name="الكورس", null=True, blank=True)
    week           = models.CharField(max_length=10, choices=WEEK_CHOICES, verbose_name="الأسبوع", null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة", null=True, blank=True)

    # الحقل الجديد لرفع PDF
    pdf            = models.FileField(
                        upload_to="lecture_pdfs/",
                        verbose_name="ملف PDF للمحاضرة",
                        blank=True,
                        null=True
                     )

    def __str__(self):
        grade_disp  = dict(GRADE_CHOICES).get(self.grade, "غير محدد")
        week_disp   = self.get_week_display() if self.week else "غير محدد"
        course_name = self.course.title if self.course else "بدون كورس"
        return f"{self.title} – {grade_disp} – {course_name} – {week_disp}"



# ─── نموذج الامتحان ──────────────────────────────────────────────────────
class Exam(models.Model):
    title           = models.CharField(max_length=255, verbose_name="عنوان الامتحان")
    description     = models.TextField(verbose_name="الوصف", null=True, blank=True)
    grade           = models.CharField(max_length=10, choices=GRADE_CHOICES, verbose_name="الصف الدراسي", null=True, blank=True)
    course          = models.ForeignKey("content.Course", on_delete=models.CASCADE, verbose_name="الكورس", null=True, blank=True)
    week            = models.CharField(max_length=10, choices=WEEK_CHOICES, verbose_name="الأسبوع", null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة", null=True, blank=True)
    total_mcq_score = models.PositiveIntegerField(default=0, verbose_name="المجموع الكلي للاختيارات")
    duration_minutes= models.PositiveIntegerField(default=30, verbose_name="مدة الامتحان (دقائق)")

    def distribute_mcq_scores(self):
        mcq_qs = self.questions.filter(question_type='mcq')
        count  = mcq_qs.count()
        if count and self.total_mcq_score:
            per = self.total_mcq_score / count
            for q in mcq_qs:
                q.score = round(per, 2)
                q.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.distribute_mcq_scores()

    def __str__(self):
        grade_disp = dict(GRADE_CHOICES).get(self.grade, "غير محدد")
        week_disp  = self.get_week_display() if self.week else "غير محدد"
        return f"{self.title} – {grade_disp} – {week_disp}"


# ─── نموذج الأسئلة ────────────────────────────────────────────────────────
class Question(models.Model):
    exam          = models.ForeignKey("content.Exam", on_delete=models.CASCADE, related_name="questions",
                                      verbose_name="الامتحان", null=True, blank=True)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES,
                                     verbose_name="نوع السؤال", null=True, blank=True)
    text          = models.TextField(verbose_name="نص السؤال", null=True, blank=True)
    image         = models.ImageField(upload_to="questions/", verbose_name="صورة السؤال", null=True, blank=True)
    score         = models.FloatField(default=0, verbose_name="درجة السؤال", editable=False)

    def __str__(self):
        return f"{self.get_question_type_display()} – {self.text[:30] if self.text else 'بدون نص'}"


# ─── نموذج الاختيارات ─────────────────────────────────────────────────────
class Choice(models.Model):
    question   = models.ForeignKey("content.Question", on_delete=models.CASCADE, related_name="choices", verbose_name="السؤال", null=True, blank=True)
    text       = models.CharField(max_length=255, verbose_name="نص الإجابة", null=True, blank=True)
    is_correct = models.BooleanField(default=False, verbose_name="إجابة صحيحة")

    def __str__(self):
        return f"{self.text} {'✅' if self.is_correct else ''}"


# ─── نموذج حضور المحاضرات ─────────────────────────────────────────────────
class LectureAttendance(models.Model):
    STATUS_CHOICES = [('absent','غائب'), ('present','حاضر')]

    student   = models.ForeignKey("accounts.Student", on_delete=models.CASCADE,
                                  related_name='lecture_attendances', verbose_name="الطالب")
    lecture   = models.ForeignKey("content.Lecture", on_delete=models.CASCADE,
                                  related_name='attendances',      verbose_name="المحاضرة")
    status    = models.CharField(max_length=7, choices=STATUS_CHOICES, verbose_name="الحالة")
    timestamp = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        unique_together     = ('student','lecture')
        verbose_name        = "حضور محاضرة"
        verbose_name_plural = "سجلات حضور المحاضرات"

    def __str__(self):
        return f"{self.student} – {self.lecture.title}: {self.get_status_display()}"


# ─── نموذج حضور الامتحانات ─────────────────────────────────────────────────
class ExamAttendance(models.Model):
    STATUS_CHOICES = [('absent','غائب'), ('present','حاضر')]

    student   = models.ForeignKey("accounts.Student", on_delete=models.CASCADE,
                                  related_name='exam_attendances', verbose_name="الطالب")
    exam      = models.ForeignKey("content.Exam", on_delete=models.CASCADE,
                                  related_name='attendances', verbose_name="الامتحان")
    status    = models.CharField(max_length=7, choices=STATUS_CHOICES, verbose_name="الحالة")
    timestamp = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        unique_together     = ('student','exam')
        verbose_name        = "حضور امتحان"
        verbose_name_plural = "سجلات حضور الامتحانات"

    def __str__(self):
        return f"{self.student} – {self.exam.title}: {self.get_status_display()}"
