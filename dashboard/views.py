from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import Count, Q
from django.forms import modelform_factory, inlineformset_factory
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from .decorators import staff_required
from .registry import REGISTRY, get_config

from content.models import (
    Course, Lecture, Exam, Question, Choice, TopStudent,
    LectureAttendance, ExamAttendance,
)
from accounts.models import Student, Subscription, ActivityLog


# ──────────────────────────────────────────────────────────────
# تسجيل الدخول / الخروج
# ──────────────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard:home')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('dashboard:home')
        error = "بيانات الدخول غير صحيحة، أو ليس لديك صلاحية الوصول إلى لوحة التحكم."

    return render(request, 'dashboard/login.html', {'error': error})


@staff_required
def logout_view(request):
    logout(request)
    return redirect('dashboard:login')


# ──────────────────────────────────────────────────────────────
# الصفحة الرئيسية للوحة التحكم
# ──────────────────────────────────────────────────────────────
@staff_required
def home(request):
    stats = {
        'students_count': Student.objects.count(),
        'courses_count': Course.objects.count(),
        'lectures_count': Lecture.objects.count(),
        'exams_count': Exam.objects.count(),
        'questions_count': Question.objects.count(),
        'active_subscriptions': Subscription.objects.filter(is_active=True).count(),
        'top_students_count': TopStudent.objects.count(),
    }
    recent_activity = (
        ActivityLog.objects.select_related('student', 'lecture', 'exam')
        .order_by('-created_at')[:10]
    )
    return render(request, 'dashboard/home.html', {
        'stats': stats,
        'recent_activity': recent_activity,
        'registry': REGISTRY,
        'active_nav': 'home',
    })


# ──────────────────────────────────────────────────────────────
# CRUD عام (يخدم: الكورسات - المحاضرات - الامتحانات - الطلاب الأوائل - الاشتراكات - الطلاب)
# ──────────────────────────────────────────────────────────────
def _config_or_404(model_slug):
    config = get_config(model_slug)
    if not config:
        raise Http404("قسم غير موجود")
    return config


@staff_required
def generic_list(request, model_slug):
    config = _config_or_404(model_slug)
    model = config['model']
    qs = model.objects.all().order_by('-id')

    query = request.GET.get('q', '').strip()
    if query and config.get('search_fields'):
        q_filter = Q()
        for field_name in config['search_fields']:
            q_filter |= Q(**{f'{field_name}__icontains': query})
        qs = qs.filter(q_filter)

    return render(request, 'dashboard/generic_list.html', {
        'config': config,
        'model_slug': model_slug,
        'objects': qs,
        'query': query,
        'active_nav': model_slug,
    })


@staff_required
def generic_add(request, model_slug):
    config = _config_or_404(model_slug)
    model = config['model']
    FormClass = modelform_factory(model, fields=config['form_fields'], widgets=config.get('widgets'))

    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            _after_save(model_slug, obj)
            messages.success(request, f"تم إضافة {config['label_singular']} بنجاح ✅")
            return redirect('dashboard:list', model_slug=model_slug)
    else:
        form = FormClass()

    return render(request, 'dashboard/generic_form.html', {
        'config': config, 'model_slug': model_slug, 'form': form, 'is_edit': False,
        'active_nav': model_slug,
    })


@staff_required
def generic_edit(request, model_slug, pk):
    config = _config_or_404(model_slug)
    model = config['model']
    obj = get_object_or_404(model, pk=pk)
    FormClass = modelform_factory(model, fields=config['form_fields'], widgets=config.get('widgets'))

    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            obj = form.save()
            _after_save(model_slug, obj)
            messages.success(request, f"تم تعديل {config['label_singular']} بنجاح ✅")
            return redirect('dashboard:list', model_slug=model_slug)
    else:
        form = FormClass(instance=obj)

    return render(request, 'dashboard/generic_form.html', {
        'config': config, 'model_slug': model_slug, 'form': form, 'is_edit': True, 'obj': obj,
        'active_nav': model_slug,
    })


@staff_required
def generic_delete(request, model_slug, pk):
    config = _config_or_404(model_slug)
    model = config['model']
    obj = get_object_or_404(model, pk=pk)

    if request.method == 'POST':
        obj.delete()
        messages.success(request, f"تم حذف {config['label_singular']} بنجاح 🗑️")
        return redirect('dashboard:list', model_slug=model_slug)

    return render(request, 'dashboard/confirm_delete.html', {
        'config': config, 'model_slug': model_slug, 'obj': obj,
        'active_nav': model_slug,
    })


def _after_save(model_slug, obj):
    """منطق إضافي بعد الحفظ - مثال: الاشتراك الجماعي لصف دراسي كامل دفعة واحدة."""
    if model_slug == 'subscriptions' and obj.target_grade and not obj.student:
        students = Student.objects.filter(grade=obj.target_grade)
        for student in students:
            sub, _created = Subscription.objects.get_or_create(
                student=student, year=obj.year,
                defaults={'is_active': obj.is_active},
            )
            sub.courses.set(obj.courses.all())
            sub.is_active = obj.is_active
            sub.save()


# ──────────────────────────────────────────────────────────────
# إدارة الأسئلة والاختيارات (Question + Choice) - تحتاج فورم خاص لأنها متداخلة
# ──────────────────────────────────────────────────────────────
QuestionFormClass = modelform_factory(Question, fields=['exam', 'question_type', 'text', 'image'])
ChoiceFormSet = inlineformset_factory(
    Question, Choice, fields=['text', 'is_correct'], extra=4, can_delete=True,
)


@staff_required
def question_list(request, exam_id=None):
    qs = Question.objects.select_related('exam').all().order_by('-id')
    if exam_id:
        qs = qs.filter(exam_id=exam_id)
    exams = Exam.objects.all()
    return render(request, 'dashboard/question_list.html', {
        'questions': qs, 'exams': exams, 'selected_exam': exam_id,
        'active_nav': 'questions',
    })


@staff_required
def question_add(request):
    if request.method == 'POST':
        form = QuestionFormClass(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                question = form.save()
                formset = ChoiceFormSet(request.POST, instance=question)
                if formset.is_valid():
                    formset.save()
                    if question.exam:
                        question.exam.distribute_mcq_scores()
                    messages.success(request, "تم إضافة السؤال بنجاح ✅")
                    return redirect('dashboard:question_list')
                transaction.set_rollback(True)
        else:
            formset = ChoiceFormSet(request.POST)
    else:
        form = QuestionFormClass()
        formset = ChoiceFormSet()

    return render(request, 'dashboard/question_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
        'active_nav': 'questions',
    })


@staff_required
def question_edit(request, pk):
    question = get_object_or_404(Question, pk=pk)

    if request.method == 'POST':
        form = QuestionFormClass(request.POST, request.FILES, instance=question)
        formset = ChoiceFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            if question.exam:
                question.exam.distribute_mcq_scores()
            messages.success(request, "تم تعديل السؤال بنجاح ✅")
            return redirect('dashboard:question_list')
    else:
        form = QuestionFormClass(instance=question)
        formset = ChoiceFormSet(instance=question)

    return render(request, 'dashboard/question_form.html', {
        'form': form, 'formset': formset, 'is_edit': True, 'question': question,
        'active_nav': 'questions',
    })


@staff_required
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        question.delete()
        messages.success(request, "تم حذف السؤال بنجاح 🗑️")
        return redirect('dashboard:question_list')
    return render(request, 'dashboard/confirm_delete.html', {
        'obj': question,
        'config': {'label_singular': 'السؤال'},
        'model_slug': None,
        'cancel_url_name': 'dashboard:question_list',
        'delete_url_name': 'dashboard:question_delete',
        'active_nav': 'questions',
    })


# ──────────────────────────────────────────────────────────────
# سجل النشاط (قراءة فقط)
# ──────────────────────────────────────────────────────────────
@staff_required
def activity_log_list(request):
    qs = ActivityLog.objects.select_related('student', 'lecture', 'exam').order_by('-created_at')

    student_q = request.GET.get('student', '').strip()
    type_q = request.GET.get('type', '').strip()

    if student_q:
        qs = qs.filter(
            Q(student__full_name__icontains=student_q) |
            Q(student__parent_phone_number__icontains=student_q)
        )
    if type_q:
        qs = qs.filter(activity_type=type_q)

    return render(request, 'dashboard/activity_log.html', {
        'logs': qs[:300],
        'student_q': student_q,
        'type_q': type_q,
        'activity_types': ActivityLog.ACTIVITY_TYPES,
        'active_nav': 'activity-log',
    })


# ──────────────────────────────────────────────────────────────
# الحضور والغياب (محاضرات / امتحانات) - قراءة فقط
# ──────────────────────────────────────────────────────────────
@staff_required
def lecture_attendance(request, lecture_id):
    lecture = get_object_or_404(Lecture, pk=lecture_id)
    present = LectureAttendance.objects.filter(lecture=lecture, status='present').select_related('student')
    absent = LectureAttendance.objects.filter(lecture=lecture, status='absent').select_related('student')
    return render(request, 'dashboard/attendance.html', {
        'title': f'الحضور والغياب — {lecture.title}',
        'present': present, 'absent': absent,
        'back_url': 'dashboard:list', 'back_slug': 'lectures',
        'active_nav': 'lectures',
    })


@staff_required
def exam_attendance(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    present = ExamAttendance.objects.filter(exam=exam, status='present').select_related('student')
    absent = ExamAttendance.objects.filter(exam=exam, status='absent').select_related('student')
    return render(request, 'dashboard/attendance.html', {
        'title': f'الحضور والغياب — {exam.title}',
        'present': present, 'absent': absent,
        'back_url': 'dashboard:list', 'back_slug': 'exams',
        'active_nav': 'exams',
    })


# ──────────────────────────────────────────────────────────────
# تكرارات الطلاب (نفس فكرة أداة التكرارات في أدمين Django القديم)
# ──────────────────────────────────────────────────────────────
@staff_required
def student_duplicates(request):
    if request.method == 'POST' and request.POST.get('action') == 'delete_selected':
        ids = request.POST.getlist('delete_ids')
        if ids:
            qs = Student.objects.filter(id__in=ids)
            count = qs.count()
            qs.delete()
            messages.success(request, f"تم حذف {count} سجل مكرر 🗑️")
        return redirect('dashboard:student_duplicates')

    dup_parents = (Student.objects.exclude(parent_phone_number__isnull=True)
                   .exclude(parent_phone_number='')
                   .values('parent_phone_number')
                   .annotate(cnt=Count('id')).filter(cnt__gt=1))
    parent_groups = [
        {'key': item['parent_phone_number'],
         'members': list(Student.objects.filter(parent_phone_number=item['parent_phone_number']).order_by('id'))}
        for item in dup_parents
    ]

    return render(request, 'dashboard/student_duplicates.html', {
        'parent_groups': parent_groups,
        'active_nav': 'duplicates',
    })
