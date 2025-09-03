from . import views
from django.urls import path
from .views import register_student
from .views import course_page, protected_video

app_name = 'accounts' 

urlpatterns = [
    path('', views.home, name='home'),

    path('register/', register_student, name='register_student'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    
    path('profile/', views.profile, name='profile'),

    path('courses/', course_page, name='course_page'),
    path('video/<int:video_id>/', protected_video, name='protected_video'),

    path("header/", views.header_view, name="header"),
    path("section2/", views.section2_view, name="section2"),
    path("second-section/", views.second_section_view, name="second_section"),
    path("section-three/", views.section3_view, name="section3"),
    path("footer/", views.footer_view, name="footer"),
    path("stages/", views.stages_view, name="stages"),
    path("phase/", views.phase_view, name="phase"),

    path('page4/', views.page_4, name='page_4'),
    path('page5/', views.page_5, name='page_5'),
    path('page6/', views.page_6, name='page_6'),
    path('course-page-7/', views.course_page_7, name='course_page_7'),
    path('page8/', views.page_8, name='page_8'),
    path('page9/', views.page_9, name='page_9'),
    path('course-page-10/', views.course_page_10, name='course_page_10'),
    path('course-page-12/', views.course_page_12, name='course_page_12'),


]
