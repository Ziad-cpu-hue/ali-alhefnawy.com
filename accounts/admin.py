from django.contrib import admin
from django import forms
from django.utils.html import format_html
from .models import Student, Subscription  # تمت إزالة MonthlyCourse من الاستيراد

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 
        'last_name', 
        'phone_number', 
        'parent_phone_number', 
        'governorate', 
        'grade', 
        'get_exams_completed',  # حساب عدد الامتحانات المكتملة ديناميكيًا
        'get_average_score',      # حساب متوسط الدرجة ديناميكيًا
        'total_lecture_time', 
        'total_video_views', 
        'total_exam_views', 
        'total_exam_completions',
    )
    search_fields = (
        'first_name', 
        'last_name', 
        'phone_number', 
        'governorate',
    )
    list_filter = (
        'grade', 
        'governorate',
    )
    readonly_fields = (
        'total_lecture_time', 
        'total_video_views', 
        'total_exam_views', 
        'total_exam_completions',
    )
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': (
                'first_name', 
                'last_name', 
                'phone_number', 
                'parent_phone_number', 
                'governorate', 
                'grade',
            ),
        }),
        ('إحصائيات المنصة', {
            'fields': (
                'total_lecture_time', 
                'total_video_views', 
                'total_exam_views', 
                'total_exam_completions',
            ),
        }),
    )

    def get_exams_completed(self, obj):
        """إرجاع عدد الامتحانات المكتملة"""
        return obj.attempted_exams.count()
    get_exams_completed.short_description = "عدد الامتحانات المكتملة"

    def get_average_score(self, obj):
        """إرجاع متوسط الدرجة بناءً على الامتحانات المكتملة"""
        completed_exams = obj.attempted_exams.all()
        if completed_exams:
            total_score = sum(
                sum(question.score for question in exam.questions.all())
                for exam in completed_exams
            )
            return round(total_score / len(completed_exams), 2)
        return 0
    get_average_score.short_description = "متوسط الدرجة"


from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import datetime

from .models import Subscription, Student
from content.models import Course

# ─── نموذج مخصص في نفس الملف ───────────────────────────────────────────
class SubscriptionAdminForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # عرض جميع الطلاب والكورسات
        self.fields['student'].queryset = Student.objects.all()
        self.fields['courses'].queryset = Course.objects.all()


# ─── تسجيل Subscription في لوحة الإدارة ─────────────────────────────────
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    form = SubscriptionAdminForm
    list_display = (
        'student',
        'target_grade',
        'get_course_name',
        'year',
        'is_active',
    )
    list_filter = (
        'is_active',
        'year',
        'target_grade',
    )
    search_fields = (
        'student__first_name',
        'student__last_name',
        'target_grade',
    )
    autocomplete_fields = ['student']

    actions = [
        'activate_selected_subscriptions',
        'deactivate_selected_subscriptions',
    ]

    def get_course_name(self, obj):
        return ", ".join([c.title for c in obj.courses.all()])
    get_course_name.short_description = _('اسم الكورسات')

    def activate_selected_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f"تم تفعيل {updated} اشتراك بنجاح"))
    activate_selected_subscriptions.short_description = _("تفعيل الاشتراكات المحددة")

    def deactivate_selected_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f"تم إلغاء تفعيل {updated} اشتراك بنجاح"))
    deactivate_selected_subscriptions.short_description = _("إلغاء تفعيل الاشتراكات المحددة")

    # ─── هنا نحقّق “الاشتراك الجماعي” عند الحفظ ───────────────────────────
    def save_model(self, request, obj, form, change):
        # احفظ الاشتراك الأصلي أولاً
        super().save_model(request, obj, form, change)

        # إذا كان لدينا صف محدد فقط (بدون طالب)
        if obj.target_grade and not obj.student:
            # جلب جميع الطلاب في هذا الصف
            students = Student.objects.filter(grade=obj.target_grade)
            for student in students:
                sub, created = Subscription.objects.get_or_create(
                    student=student,
                    year=obj.year,
                    defaults={'is_active': obj.is_active}
                )
                # انسخ الكورسات وحالة التفعيل
                sub.courses.set(obj.courses.all())
                sub.is_active = obj.is_active
                sub.save()
