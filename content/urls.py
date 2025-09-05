from . import views  # ✅ تأكد من استيراد views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import home, lecture_detail, exam_detail, submit_exam, exam_analysis

urlpatterns = [

    # ✅ ضع المسار المحدّد أولاً
    path('top-students-page/', views.top_students_page, name='top_students_page'),
    
    # --- خرائط ثابتة لدرجات الإعدادية (تحويل لمسارات رقيمة متوافقة مع models) ---
    path("first/", views.course_list, {'grade': '4'}, name='course_first'),
    path("second/", views.course_list, {'grade': '5'}, name='course_second'),
    path("third/", views.course_list, {'grade': '6'}, name='course_third'),

    path("home/<str:grade>/<int:course_id>/", views.home, name="home_filtered"),
    path("lecture/<int:lecture_id>/", lecture_detail, name="lecture_detail"),
    path("exam/<int:exam_id>/", exam_detail, name="exam_detail"),
    #""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    path("exam/<int:exam_id>/submit/", submit_exam, name="submit_exam"),
    path("exam/<int:exam_id>/analysis/", exam_analysis, name="exam_analysis"),

    path("subscriptions/", views.subscriptions, name="subscriptions"),

    #""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    path('', views.course_list, name='course_list'),
    path('<str:grade>/', views.course_list, name='course_list_by_grade'),
    #############################################################################################
    path("lecture/<int:lecture_id>/progress/", views.update_watch_progress, name="update_watch_progress"),

]

# ✅ إضافة دعم لعرض الفيديوهات والملفات المرفوعة أثناء التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

