from django.db import models

# خيارات الصف الدراسي
GRADE_CHOICES = [
    ('first', 'الصف الأول'),
    ('second', 'الصف الثاني'),
    ('third', 'الصف الثالث'),
]

# خيارات الأسابيع داخل الكورس
WEEK_CHOICES = [
    ('week1', 'الأسبوع الأول'),
    ('week2', 'الأسبوع الثاني'),
    ('week3', 'الأسبوع الثالث'),
    ('week4', 'الأسبوع الرابع'),
]

# أنواع الأسئلة
QUESTION_TYPE_CHOICES = [
    ('mcq', 'اختياري'),
    ('essay', 'مقالي'),
]

class Lecture(models.Model):
    title = models.CharField(max_length=255, verbose_name="عنوان المحاضرة")
    description = models.TextField(verbose_name="الوصف", null=True, blank=True)
    video = models.FileField(upload_to="videos/", verbose_name="ملف الفيديو", blank=True, null=True)
    # حقل جديد لتخزين رابط YouTube للفيديو
    youtube_iframe = models.TextField(verbose_name="كود تضمين فيديو YouTube", blank=True, null=True)

    grade = models.CharField(max_length=10, choices=GRADE_CHOICES, verbose_name="الصف الدراسي", null=True, blank=True)
    # تم تعديل العلاقة لتشير إلى نموذج Course بدلاً من Card
    course = models.ForeignKey("Course", on_delete=models.CASCADE, verbose_name="كورس الشهر", null=True, blank=True)
    week = models.CharField(max_length=10, choices=WEEK_CHOICES, verbose_name="الأسبوع", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة", null=True, blank=True)
    # duration = models.PositiveIntegerField(default=0, verbose_name="مدة المحاضرة (بالدقائق)")

    def __str__(self):
        course_name = self.course.title if self.course else "بدون كورس"
        week_display = self.get_week_display() if self.week else "غير محدد"
        return f"{self.title} - {self.get_grade_display()} - {course_name} - {week_display}"




class Exam(models.Model):
    title = models.CharField(max_length=255, verbose_name="عنوان الامتحان")
    description = models.TextField(verbose_name="الوصف", null=True, blank=True)
    grade = models.CharField(max_length=10, choices=GRADE_CHOICES, verbose_name="الصف الدراسي", null=True, blank=True)
    course = models.ForeignKey("Course", on_delete=models.CASCADE, verbose_name="كورس الشهر", null=True, blank=True)
    week = models.CharField(max_length=10, choices=WEEK_CHOICES, verbose_name="الأسبوع", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة", null=True, blank=True)
    total_mcq_score = models.PositiveIntegerField(default=0, verbose_name="المجموع الكلي للأسئلة الاختيارية")
    duration_minutes = models.PositiveIntegerField(default=30, verbose_name="مدة الامتحان بالدقائق")  # تم التعديل هنا

    def distribute_mcq_scores(self):
        """توزيع الدرجات تلقائيًا على الأسئلة الاختيارية"""
        mcq_questions = self.questions.filter(question_type='mcq')
        num_mcq = mcq_questions.count()
        if num_mcq > 0 and self.total_mcq_score > 0:
            score_per_question = self.total_mcq_score / num_mcq
            for question in mcq_questions:
                question.score = round(score_per_question, 2)
                question.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.distribute_mcq_scores()

    def __str__(self):
        week_display = self.get_week_display() if self.week else "غير محدد"
        return f"{self.title} - {self.get_grade_display()} - {week_display}"




class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions", verbose_name="الامتحان", null=True, blank=True)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES, verbose_name="نوع السؤال", null=True, blank=True)
    text = models.TextField(verbose_name="نص السؤال", null=True, blank=True)
    image = models.ImageField(upload_to="questions/", verbose_name="صورة السؤال", null=True, blank=True)
    score = models.FloatField(default=0, verbose_name="درجة السؤال", editable=False)

    def __str__(self):
        return f"{self.get_question_type_display()} - {self.text[:30] if self.text else 'صورة'}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices", verbose_name="السؤال", null=True, blank=True)
    text = models.CharField(max_length=255, verbose_name="نص الإجابة", null=True, blank=True)
    is_correct = models.BooleanField(default=False, verbose_name="إجابة صحيحة")

    def __str__(self):
        return f"{self.text} {'✅' if self.is_correct else ''}"


# نموذج الكورسات - أصبح يعتمد الآن على Course وهو الأساس الذي يعتمد عليه Lecture و Exam
class Course(models.Model):
    GRADE_CHOICES = [
        ('first', 'الصف الأول'),
        ('second', 'الصف الثاني'),
        ('third', 'الصف الثالث'),
    ]
    
    title = models.CharField(max_length=255, verbose_name="عنوان الكورس")
    description = models.TextField(verbose_name="الوصف")
    image = models.ImageField(upload_to='course_images/', verbose_name="الصورة")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    grade = models.CharField(
        max_length=10,
        choices=GRADE_CHOICES,
        verbose_name="الصف الدراسي",
        default="first"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ آخر تحديث")

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return f"{self.title} - {self.get_grade_display()}"
