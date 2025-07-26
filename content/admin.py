from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django import forms
from .models import (
    Lecture, Exam, Question, Choice, Course,
    LectureAttendance, ExamAttendance
)

# ── إلغاء تسجيل Lecture و Exam إذا تم تسجيلهم مسبقًا ─────────────
for model in (Lecture, Exam):
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass

# ───────────────────────────
# 🔄 Base Inline حضور
# ───────────────────────────
class BaseAttendanceInline(admin.TabularInline):
    fields = ('student',)
    readonly_fields = ('student',)
    extra = 0

# ───────────────────────────
# ✅ حضور المحاضرات - حاضر
# ───────────────────────────
class LecturePresentInline(BaseAttendanceInline):
    model = LectureAttendance
    verbose_name = "طالب حضر"
    verbose_name_plural = "الحاضرون"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='present')

# ───────────────────────────
# ❌ حضور المحاضرات - غائب
# ───────────────────────────
class LectureAbsentInline(BaseAttendanceInline):
    model = LectureAttendance
    verbose_name = "طالب غائب"
    verbose_name_plural = "الغائبون"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='absent')

# ───────────────────────────
# 🎓 إعداد لوحة المحاضرات
# ───────────────────────────
@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display  = ('title', 'course', 'grade', 'week', 'created_at')
    search_fields = ('title',)
    list_filter   = ('grade', 'course', 'week')
    inlines       = [LecturePresentInline, LectureAbsentInline]

    # لإظهار حقل رفع PDF في شاشة التعديل
    fields = (
        'title', 'description', 'video', 'youtube_iframe',
        'course', 'grade', 'week',
        'pdf',                    # ← أضف هذا
        'created_at',
    )
    readonly_fields = ('created_at',)


# ───────────────────────────
# ✅ حضور الامتحانات - حاضر
# ───────────────────────────
class ExamPresentInline(BaseAttendanceInline):
    model = ExamAttendance
    verbose_name = "طالب حضر"
    verbose_name_plural = "الحاضرون"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='present')

# ───────────────────────────
# ❌ حضور الامتحانات - غائب
# ───────────────────────────
class ExamAbsentInline(BaseAttendanceInline):
    model = ExamAttendance
    verbose_name = "طالب غائب"
    verbose_name_plural = "الغائبون"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='absent')

# ───────────────────────────
# 📝 إعداد لوحة الامتحانات
# ───────────────────────────
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display  = ('title', 'course', 'grade', 'week', 'created_at', 'total_mcq_score')
    search_fields = ('title',)
    list_filter   = ('grade', 'course', 'week')
    inlines       = [ExamPresentInline, ExamAbsentInline]

# ───────────────────────────
# 🧠 إعدادات الأسئلة والاختيارات
# ───────────────────────────
class ChoiceInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    formset = ChoiceInlineFormSet
    class Media:
        js = ('admin/js/choice_inline.js',)

class QuestionAdminForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    list_display  = ("text", "question_type", "exam")
    search_fields = ("text",)
    list_filter   = ("question_type", "exam")
    inlines       = [ChoiceInline]

# ───────────────────────────
# 🎓 إعداد الكورسات
# ───────────────────────────
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'grade', 'price', 'created_at')
    list_filter  = ('grade',)
