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


from django import forms
from django.contrib import admin
from accounts.models import Subscription, Student
from content.models import Course

# ✅ نموذج مخصص لإدارة الاشتراكات
from django import forms
from django.contrib import admin
from accounts.models import Subscription, Student
from content.models import Course

# نموذج مخصص لإدارة الاشتراكات
class SubscriptionAdminForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.all()
        # تم استبدال Card بـ Course واستخدام الحقل الصحيح "courses"
        self.fields["courses"].queryset = Course.objects.all()

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    form = SubscriptionAdminForm
    list_display = ('student', 'get_course_name', 'year', 'is_active')
    list_filter = ('is_active', 'year')
    search_fields = (
        'student__user__username', 
        'student__user__first_name', 
        'student__user__last_name', 
        'courses__title'
    )
    autocomplete_fields = ['student']

    actions = ['activate_selected_subscriptions', 'deactivate_selected_subscriptions']

    def get_course_name(self, obj):
        # بما أن "courses" حقل متعدد (ManyToMany)، نقوم بعرض أسماء الكورسات مفصولة بفاصلة
        return ", ".join([course.title for course in obj.courses.all()])
    get_course_name.short_description = 'اسم الكورس'

    def activate_selected_subscriptions(self, request, queryset):
        updated_count = queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {updated_count} اشتراك بنجاح.")
    activate_selected_subscriptions.short_description = "تفعيل الاشتراكات المحددة"

    def deactivate_selected_subscriptions(self, request, queryset):
        updated_count = queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {updated_count} اشتراك بنجاح.")
    deactivate_selected_subscriptions.short_description = "إلغاء تفعيل الاشتراكات المحددة"


###################################################################

from django.contrib import admin
from .models import PaymentRequest, Enrollment

@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('id','student','course','amount_required','txn_id','paid','created_at')
    readonly_fields = ('_phash',)
    list_filter = ('paid','created_at')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student','course','active','enrolled_at')
