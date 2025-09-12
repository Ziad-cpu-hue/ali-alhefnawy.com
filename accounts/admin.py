from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import datetime

from .models import Student, Subscription, ActivityLog  # أضفنا ActivityLog هنا
from content.models import Course

# إضافات جديدة للـ admin (URLs, عرض وحذف التكرارات)
from django.urls import path, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.db.models import Count
from django.utils.html import escape


# ──────────────────────────────────────────────────────────────────────────────
# Inline لعرض سجلات النشاط داخل صفحة Student في الأدمين
# ──────────────────────────────────────────────────────────────────────────────
class ActivityLogInline(admin.TabularInline):
    model = ActivityLog
    extra = 0
    readonly_fields = ('activity_type', 'lecture', 'exam', 'score', 'details', 'created_at')
    can_delete = False
    verbose_name = "سجل نشاط"
    verbose_name_plural = "سجلات النشاط"
    ordering = ('-created_at',)


# ──────────────────────────────────────────────────────────────────────────────
# تسجيل Student في لوحة الإدارة (مع إضافة الـ Inline لسجلات النشاط)
# تمت إضافة view جديدة لعرض التكرارات وحذفها من الأدمِن فقط دون تغيير باقي المنطق
# ──────────────────────────────────────────────────────────────────────────────
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
        'get_average_score',    # حساب متوسط الدرجة ديناميكيًا
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

    # إضافة inline لسجلات النشاط (لن يكسر الوظائف الأصلية)
    inlines = [ActivityLogInline]

    # إتاحة روابط عرض التكرارات في قائمة الأكشنات عبر إضافة URL مخصص
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('duplicates/', self.admin_site.admin_view(self.duplicates_view), name='students_duplicates'),
        ]
        return my_urls + urls

    def duplicates_view(self, request):
        """
        GET: يعرض صفحة تحتوي على المجموعات المتكررة (رقم الهاتف - رقم ولي الأمر - مطابقات أخرى)
        POST: يحذف الـ IDs المرسلة في الحقل delete_ids
        ملاحظة: هذه الأداة مخصصة لمديري النظام عبر الأدمِن. الحذف نهائي (استخدمها بحذر).
        """
        # تنفيذ عملية الحذف لو جاءت POST مع delete_ids
        if request.method == 'POST' and request.POST.get('action') == 'delete_selected':
            ids = request.POST.getlist('delete_ids')
            if ids:
                qs = Student.objects.filter(id__in=ids)
                count = qs.count()
                qs.delete()
                # بعد الحذف نعيد توجيه المستخدم إلى نفس الصفحة مع رسالة بسيطة عبر GET parameter
                return HttpResponseRedirect(reverse('admin:students_duplicates') + f'?deleted={count}')

        # جلب مجموعات التكرارات حسب phone_number و parent_phone_number
        duplicate_phones = Student.objects.values('phone_number').annotate(cnt=Count('id')).filter(phone_number__isnull=False).filter(cnt__gt=1)
        duplicate_parents = Student.objects.values('parent_phone_number').annotate(cnt=Count('id')).filter(parent_phone_number__isnull=False).filter(cnt__gt=1)

        # بناء بيانات مفصّلة لكل مجموعة
        phone_groups = []
        for item in duplicate_phones:
            num = item['phone_number']
            members = list(Student.objects.filter(phone_number=num).order_by('id'))
            phone_groups.append({
                'key': num,
                'count': item['cnt'],
                'members': members,
            })

        parent_groups = []
        for item in duplicate_parents:
            num = item['parent_phone_number']
            members = list(Student.objects.filter(parent_phone_number=num).order_by('id'))
            parent_groups.append({
                'key': num,
                'count': item['cnt'],
                'members': members,
            })

        # نتائج الحذف (إن وُجدت)
        deleted_count = request.GET.get('deleted')

        # بناء HTML للعرض داخل صفحة الأدمِن (أسلوب بسيط ومتوافق مع لوحة الأدمِن)
        csrf_token = get_token(request)
        admin_site_url = reverse('admin:index')
        students_change_url = reverse('admin:content_student_changelist') if False else None  # placeholder (لا نستخدمها مباشرة)
        html_parts = []
        html_parts.append(f"<h1>التكرارات في الطلاب</h1>")
        html_parts.append(f"<p><a href='{admin_site_url}'>العودة للوحة التحكم</a></p>")
        if deleted_count:
            html_parts.append(f"<p style='color:green'>تم حذف {escape(deleted_count)} سجل(س).</p>")

        html_parts.append("<form method='post'>")
        html_parts.append(f"<input type='hidden' name='csrfmiddlewaretoken' value='{csrf_token}' />")
        html_parts.append("<input type='hidden' name='action' value='delete_selected' />")

        # عرض مجموعات أرقام الهاتف المتكررة
        html_parts.append("<h2>التكرارات حسب رقم الطالب (phone_number)</h2>")
        if phone_groups:
            for grp in phone_groups:
                html_parts.append(f"<div style='border:1px solid #ddd;padding:8px;margin-bottom:12px'>")
                html_parts.append(f"<strong>الرقم: {escape(grp['key'])} — عدد السجلات: {grp['count']}</strong><br/>")
                html_parts.append("<table style='width:100%;border-collapse:collapse;margin-top:6px'>")
                html_parts.append("<tr><th style='text-align:left;padding:6px'>اختيار</th><th style='text-align:left;padding:6px'>ID</th><th style='text-align:left;padding:6px'>الاسم</th><th style='text-align:left;padding:6px'>الصف</th><th style='text-align:left;padding:6px'>عرض</th></tr>")
                for s in grp['members']:
                    change_url = reverse('admin:%s_%s_change' % (s._meta.app_label, s._meta.model_name), args=[s.id])
                    html_parts.append("<tr>")
                    html_parts.append(f"<td style='padding:6px'><input type='checkbox' name='delete_ids' value='{s.id}'/></td>")
                    html_parts.append(f"<td style='padding:6px'>{s.id}</td>")
                    html_parts.append(f"<td style='padding:6px'>{escape(s.first_name)} {escape(s.last_name)}</td>")
                    html_parts.append(f"<td style='padding:6px'>{escape(str(s.grade))}</td>")
                    html_parts.append(f"<td style='padding:6px'><a href='{change_url}'>تحرير/عرض</a></td>")
                    html_parts.append("</tr>")
                html_parts.append("</table>")
                html_parts.append("</div>")
        else:
            html_parts.append("<p>لا توجد سجلات متكررة حسب رقم الطالب.</p>")

        # عرض مجموعات أرقام ولي الأمر المتكررة
        html_parts.append("<h2>التكرارات حسب رقم ولي الأمر (parent_phone_number)</h2>")
        if parent_groups:
            for grp in parent_groups:
                html_parts.append(f"<div style='border:1px solid #ddd;padding:8px;margin-bottom:12px'>")
                html_parts.append(f"<strong>الرقم: {escape(grp['key'])} — عدد السجلات: {grp['count']}</strong><br/>")
                html_parts.append("<table style='width:100%;border-collapse:collapse;margin-top:6px'>")
                html_parts.append("<tr><th style='text-align:left;padding:6px'>اختيار</th><th style='text-align:left;padding:6px'>ID</th><th style='text-align:left;padding:6px'>الاسم</th><th style='text-align:left;padding:6px'>الصف</th><th style='text-align:left;padding:6px'>عرض</th></tr>")
                for s in grp['members']:
                    change_url = reverse('admin:%s_%s_change' % (s._meta.app_label, s._meta.model_name), args=[s.id])
                    html_parts.append("<tr>")
                    html_parts.append(f"<td style='padding:6px'><input type='checkbox' name='delete_ids' value='{s.id}'/></td>")
                    html_parts.append(f"<td style='padding:6px'>{s.id}</td>")
                    html_parts.append(f"<td style='padding:6px'>{escape(s.first_name)} {escape(s.last_name)}</td>")
                    html_parts.append(f"<td style='padding:6px'>{escape(str(s.grade))}</td>")
                    html_parts.append(f"<td style='padding:6px'><a href='{change_url}'>تحرير/عرض</a></td>")
                    html_parts.append("</tr>")
                html_parts.append("</table>")
                html_parts.append("</div>")
        else:
            html_parts.append("<p>لا توجد سجلات متكررة حسب رقم ولي الأمر.</p>")

        # أزرار الإجراء
        html_parts.append("<div style='margin-top:12px'>")
        html_parts.append("<button type='submit' onclick='return confirm(\"هل أنت متأكد من حذف السجلات المحددة؟ هذه العملية لا يمكن التراجع عنها.\")'>حذف المحدد</button>")
        html_parts.append("</div>")

        html_parts.append("</form>")

        # إرشاد سريع: روابط العودة لصفحة الطلاب
        changelist_url = reverse('admin:%s_%s_changelist' % (Student._meta.app_label, Student._meta.model_name))
        html_parts.append(f"<hr/><p><a href='{changelist_url}'>العودة لقائمة الطلاب</a></p>")

        html = "\n".join(html_parts)
        return HttpResponse(html)

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


# ──────────────────────────────────────────────────────────────────────────────
# Subscription admin (بدون تغيير في المنطق الأصلي، تم الحفاظ على كل الوظائف)
# ──────────────────────────────────────────────────────────────────────────────
class SubscriptionAdminForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # عرض جميع الطلاب والكورسات
        self.fields['student'].queryset = Student.objects.all()
        self.fields['courses'].queryset = Course.objects.all()


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


# ──────────────────────────────────────────────────────────────────────────────
# تسجيل ActivityLog كـ ModelAdmin مستقل (اختياري لعرض السجلات كاملة بشكل منفصل)
# ──────────────────────────────────────────────────────────────────────────────
import json
from django.contrib import admin
from django.utils.html import format_html

# ... تأكد أن ActivityLog مستورد أو مسجّل أعلاه ...

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'activity_type', 'lecture', 'exam', 'score', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('student__first_name', 'student__last_name', 'details')
    readonly_fields = ('student', 'activity_type', 'lecture', 'exam', 'score', 'details_ar', 'created_at')
    ordering = ('-created_at',)

    def details_ar(self, obj):
        """
        يعرض حقل details بصيغة جدولية مع تسميات عربية.
        يتعامل مع dict أو نص JSON أو None.
        """
        data = obj.details or {}
        # لو البيانات مخزنة كنَص JSON، نُحاول تحويلها لقاموس
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                # إذا لم يكن JSON صالح، نرجع النص كما هو
                return format_html("<pre>{}</pre>", data)

        # خريطة مفاتيح -> تسميات عربية (أضف مفاتيحك هنا حسب الحاجة)
        labels = {
            'delta_seconds': 'الزيادة في الثواني',
            'watched_seconds': 'الثواني المشاهدة',
            'lecture_duration': 'مدة المحاضرة (ثواني)',
            'prev_watched_seconds': 'الثواني المشاهدة سابقًا',
            'prev_status': 'الحالة السابقة',
            'status': 'الحالة الحالية',
            'note': 'ملاحظة',
            'answered': 'عدد الإجابات',
            'correct_answers': 'الإجابات الصحيحة',
            'total_questions': 'إجمالي الأسئلة',
            'attendance_created': 'تم إنشاء سجل الحضور',
            'attendance_prev_status': 'حالة الحضور السابقة',
            'attendance_status': 'حالة الحضور الحالية',
            'score': 'الدرجة',
        }

        if not data:
            return "-"

        # بناء جدول HTML بسيط
        rows = []
        for key, value in data.items():
            label = labels.get(key, key)  # استخدم التسمية العربية إن وُجدت، وإلا المفتاح نفسه
            # تحويل القيم البوليانية إلى نعم/لا
            if isinstance(value, bool):
                value = 'نعم' if value else 'لا'
            # تنسيق القوائم أو القواميس بشكل بصري
            if isinstance(value, (dict, list)):
                try:
                    pretty = json.dumps(value, ensure_ascii=False, indent=2)
                    value_html = format_html("<pre style='white-space:pre-wrap'>{}</pre>", pretty)
                except Exception:
                    value_html = format_html("<pre>{}</pre>", str(value))
            else:
                value_html = format_html("{}", value)
            rows.append(f"<tr><th style='text-align:left;padding-right:8px'>{label}:</th><td>{value_html}</td></tr>")

        html = "<table style='border-collapse:collapse'>{}</table>".format("".join(rows))
        return format_html(html)

    details_ar.short_description = "تفاصيل (بالعربي)"



