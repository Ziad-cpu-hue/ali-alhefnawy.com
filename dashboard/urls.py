from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    # تسجيل الدخول / الخروج
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # الصفحة الرئيسية
    path('', views.home, name='home'),

    # الأسئلة والاختيارات (لازم تكون قبل النمط العام model_slug/ عشان الترتيب)
    path('questions/', views.question_list, name='question_list'),
    path('questions/for-exam/<int:exam_id>/', views.question_list, name='question_list_for_exam'),
    path('questions/add/', views.question_add, name='question_add'),
    path('questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),

    # سجل النشاط
    path('activity-log/', views.activity_log_list, name='activity_log'),

    # الحضور والغياب
    path('lectures/<int:lecture_id>/attendance/', views.lecture_attendance, name='lecture_attendance'),
    path('exams/<int:exam_id>/attendance/', views.exam_attendance, name='exam_attendance'),

    # تكرارات الطلاب
    path('students/duplicates/', views.student_duplicates, name='student_duplicates'),

    # CRUD عام لباقي الأقسام: courses / lectures / exams / top-students / subscriptions / students
    path('<str:model_slug>/', views.generic_list, name='list'),
    path('<str:model_slug>/add/', views.generic_add, name='add'),
    path('<str:model_slug>/<int:pk>/edit/', views.generic_edit, name='edit'),
    path('<str:model_slug>/<int:pk>/delete/', views.generic_delete, name='delete'),
]
