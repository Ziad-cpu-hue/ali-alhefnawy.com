from django.contrib import admin
from django import forms
from django.forms.models import BaseInlineFormSet
from .models import Lecture, Exam, Question, Choice, Course

# ✅ تسجيل نموذج المحاضرات
@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ('title', 'grade', 'course', 'week', 'created_at', 'youtube_iframe')
    search_fields = ('title', 'description', 'youtube_iframe')
    list_filter = ('grade', 'course', 'week', 'created_at')


# حذف التحقق الخاص بضرورة وجود إجابة صحيحة
class ChoiceInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        # تم إزالة التحقق من وجود إجابة صحيحة واحدة على الأقل


# ✅ Inline لإضافة الاختيارات داخل نموذج السؤال مع ربط الـ FormSet والجافاسكريبت المخصص
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4  # 4 اختيارات جاهزة دائمًا
    formset = ChoiceInlineFormSet

    class Media:
        js = ('admin/js/choice_inline.js',)  # تأكد من صحة مسار الملف ضمن staticfiles


# ✅ نموذج مخصص للأسئلة
class QuestionAdminForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'


# ✅ تسجيل نموذج الأسئلة وربطه بالاختيارات
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    list_display = ("text", "question_type", "exam")
    search_fields = ("text",)
    list_filter = ("question_type", "exam")
    inlines = [ChoiceInline]


# ✅ تسجيل نموذج الامتحانات مع دعم توزيع الدرجات للأسئلة الاختيارية
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'grade', 'course', 'week', 'total_mcq_score', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('grade', 'course', 'week', 'created_at')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.distribute_mcq_scores()


# ✅ تسجيل نموذج الكورسات (دون تغيير)
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'grade', 'price', 'created_at')
    list_filter = ('grade',)
