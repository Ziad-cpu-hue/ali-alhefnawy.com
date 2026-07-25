"""
سجل مركزي يصف كل قسم من أقسام لوحة التحكم الجديدة:
اسم الموديل، الحقول التي تظهر في الجدول، الحقول التي تظهر في فورم الإضافة/التعديل،
وحقول البحث. أي قسم جديد تحب تضيفه مستقبلًا يكفي تضيفه هنا كسطر واحد
من غير ما تكتب View أو Template من الصفر.
"""
from django import forms

from content.models import Course, Lecture, Exam, TopStudent
from accounts.models import Student, Subscription


REGISTRY = {
    'courses': {
        'model': Course,
        'label': 'الكورسات',
        'label_singular': 'الكورس',
        'icon': '📚',
        'list_fields': ['title', 'grade', 'price', 'created_at'],
        'form_fields': ['title', 'description', 'image', 'price', 'grade'],
        'search_fields': ['title', 'description'],
        'widgets': {'description': forms.Textarea(attrs={'rows': 4})},
    },
    'lectures': {
        'model': Lecture,
        'label': 'المحاضرات',
        'label_singular': 'المحاضرة',
        'icon': '🎬',
        'list_fields': ['title', 'course', 'grade', 'week', 'created_at'],
        'form_fields': ['title', 'description', 'video', 'youtube_iframe',
                         'grade', 'course', 'week', 'duration_seconds'],
        'search_fields': ['title'],
        'widgets': {
            'description': forms.Textarea(attrs={'rows': 3}),
            'youtube_iframe': forms.Textarea(attrs={'rows': 3, 'placeholder': 'كود تضمين YouTube <iframe> (اختياري)'}),
        },
        'extra_actions': [('attendance', 'الحضور والغياب', 'dashboard:lecture_attendance')],
    },
    'exams': {
        'model': Exam,
        'label': 'الامتحانات',
        'label_singular': 'الامتحان',
        'icon': '📝',
        'list_fields': ['title', 'course', 'grade', 'week', 'total_mcq_score', 'duration_minutes'],
        'form_fields': ['title', 'description', 'grade', 'course', 'week', 'total_mcq_score', 'duration_minutes'],
        'search_fields': ['title'],
        'widgets': {'description': forms.Textarea(attrs={'rows': 3})},
        'extra_actions': [
            ('attendance', 'الحضور والغياب', 'dashboard:exam_attendance'),
            ('questions', 'الأسئلة', 'dashboard:question_list_for_exam'),
        ],
    },
    'top-students': {
        'model': TopStudent,
        'label': 'الطلاب الأوائل',
        'label_singular': 'الطالب المتفوق',
        'icon': '🏆',
        'list_fields': ['name', 'number', 'created_at'],
        'form_fields': ['name', 'description', 'number', 'image'],
        'search_fields': ['name'],
        'widgets': {'description': forms.Textarea(attrs={'rows': 3})},
    },
    'subscriptions': {
        'model': Subscription,
        'label': 'الاشتراكات',
        'label_singular': 'الاشتراك',
        'icon': '💳',
        'list_fields': ['student', 'target_grade', 'year', 'is_active'],
        'form_fields': ['student', 'target_grade', 'courses', 'is_active'],
        'search_fields': [],
    },
    'students': {
        'model': Student,
        'label': 'الطلاب',
        'label_singular': 'الطالب',
        'icon': '👨‍🎓',
        'list_fields': ['full_name', 'parent_phone_number', 'grade', 'governorate'],
        'form_fields': ['full_name', 'parent_phone_number', 'governorate', 'grade'],
        'search_fields': ['full_name', 'parent_phone_number'],
    },
}


def get_config(model_slug):
    return REGISTRY.get(model_slug)
