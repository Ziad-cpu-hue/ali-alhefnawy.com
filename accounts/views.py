from django.http import JsonResponse 
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student
from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError


def register_student(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone_number = request.POST.get("phone_number")
        parent_phone_number = request.POST.get("parent_phone_number")
        grade = request.POST.get("grade")
        governorate = request.POST.get("governorate")
        password = request.POST.get("password")  # استقبال كلمة المرور
        
        # === تعديل مؤقت: نوقف استقبال الصورة ونعرّفها None حتى لا يحدث خطأ ===
        #avatar = request.FILES.get("avatar")  # ✅ لو عايز تفعلها تاني: أعد uncomment للسطر دا
        avatar = None  # <-- تعريف مؤقت علشان المتغير موجود لكن غير مطلوب

        # التحقق من ملء جميع الحقول الأساسية (ملاحظة: حذفنا avatar من قائمة الفحص مؤقتًا)
        if not all([first_name, last_name, phone_number, grade, governorate, password]):
            return JsonResponse({"success": False, "message": "⚠️ يرجى ملء جميع الحقول المطلوبة."})

        # التحقق من أن رقم الطالب لا يساوي رقم ولي الأمر
        if parent_phone_number and phone_number == parent_phone_number:
            return JsonResponse({"success": False, "message": "⚠️ رقم الهاتف لا يمكن أن يكون نفس رقم ولي الأمر."})

        try:
            student = Student.objects.create(
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                parent_phone_number=parent_phone_number,
                grade=grade,
                governorate=governorate,
                password=make_password(password),
                #avatar=avatar  # ✅ لو عايز تحفظ الصورة تاني: أعد uncomment للسطر دا
            )
            student.save()

            # تخزين بيانات الطالب في الجلسة
            request.session["student_id"] = student.id
            request.session["student_name"] = f"{student.first_name} {student.last_name}"
            request.session["is_registered"] = True

            messages.success(request, "تم إنشاء الحساب بنجاح!")
            return JsonResponse({"success": True, "message": "✅ تم إنشاء الحساب بنجاح!"})

        except IntegrityError as e:
            if "phone_number" in str(e):
                return JsonResponse({"success": False, "message": "⚠️ رقم الهاتف مستخدم من قبل، يرجى إدخال رقم مختلف."})
            elif "parent_phone_number" in str(e):
                return JsonResponse({"success": False, "message": "⚠️ رقم ولي الأمر مستخدم من قبل، يرجى إدخال رقم مختلف."})
            else:
                return JsonResponse({"success": False, "message": "⚠️ حدث خطأ غير متوقع أثناء الحفظ."})

        except Exception as e:
            return JsonResponse({"success": False, "message": f"⚠️ حدث خطأ: {str(e)}"})

    return render(request, "pages/register.html")

def home(request):
    # استرجاع بيانات الجلسة
    student_name = request.session.get("student_name", None)
    is_registered = request.session.get("is_registered", False)

    return render(request, 'pages/All of them.html', {
        "student_name": student_name,
        "is_registered": is_registered
    })

# تسجيل الدخول
def login(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')

        try:
            student = Student.objects.get(phone_number=phone_number)
            if check_password(password, student.password):
                request.session['student_id'] = student.id
                request.session["student_name"] = f"{student.first_name} {student.last_name}"
                request.session["is_registered"] = True
                messages.success(request, 'تم تسجيل الدخول بنجاح.')
                return redirect('/')  # إعادة التوجيه إلى الصفحة الرئيسية
            else:
                messages.error(request, 'كلمة المرور غير صحيحة')
        except Student.DoesNotExist:
            messages.error(request, 'رقم الهاتف غير مسجل')
            
    return render(request, 'pages/login.html')





def logout(request):
    # تفريغ بيانات الجلسة
    request.session.flush()
    messages.success(request, "تم تسجيل الخروج بنجاح!")
    return redirect('accounts:home')


from django.shortcuts import render, redirect
from accounts.models import Student

def profile(request):
    student_id = request.session.get("student_id")

    if not student_id:
        return redirect('accounts:login')

    try:
        student = Student.objects.get(id=student_id)
        print(f"Student Found: {student.first_name} {student.last_name}")  # ✅ تحقق من أن الاسم الأخير يظهر
    except Student.DoesNotExist:
        return redirect('accounts:register')

    return render(request, 'pages/student_profile.html', {
        "student": student,
    })






from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.db.models import Q
from accounts.models import Student, Subscription
from content.models import Course, Lecture

def course_page(request):
    # تحقق من التسجيل عبر session
    if not request.session.get("is_registered"):
        return redirect('accounts:login')

    # جلب كائن الطالب من session
    student_id = request.session.get("student_id")
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return redirect('accounts:login')

    # اشتراكات فعالة فردي أو جماعي حسب الصف
    subscriptions = Subscription.objects.filter(
        is_active=True
    ).filter(
        Q(student=student) | Q(target_grade=student.grade)
    )

    allowed_courses = Course.objects.filter(
        students__in=subscriptions
    ).distinct()

    lectures_by_week = {}
    return render(request, 'pages/index (4).html', {
        'allowed_courses': allowed_courses,
        'lectures_by_week': lectures_by_week,
    })


def protected_video(request, lecture_id):
    # تحقق من التسجيل عبر session
    if not request.session.get("is_registered"):
        return HttpResponseForbidden("Access Denied")

    # جلب الطالب
    student_id = request.session.get("student_id")
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return HttpResponseForbidden("Access Denied")

    lecture = get_object_or_404(Lecture, id=lecture_id)

    # تحقق اشتراك فردي أو جماعي
    has_access = Subscription.objects.filter(
        is_active=True
    ).filter(
        Q(student=student) | Q(target_grade=student.grade)
    ).filter(
        courses=lecture.course
    ).exists()

    if not has_access:
        return HttpResponseForbidden("Access Denied")

    return redirect(lecture.video.url)



def header_view(request):
    return render(request, "pages/header - Copy - Copy.html")

def section2_view(request):
    return render(request, "pages/section 2 - Copy - Copy - Copy - Copy - Copy.html")

def second_section_view(request):
    return render(request, "pages/Second section.html")

def section3_view(request):
    return render(request, "pages/Section Three - Copy - Copy.html")

def footer_view(request):
    return render(request, "pages/Footer.html")


def stages_view(request):
    return render(request, "pages/Stages.html")

def phase_view(request):
    return render(request, "pages/phase.html")

# عرض الصفحات الأخرى
def page_4(request):
    return render(request, 'pages/index (4).html')

def page_5(request):
    return render(request, 'pages/index (5).html')

def page_6(request):
    return render(request, 'pages/index (6).html')

def course_page_7(request):
    return render(request, 'pages/index (7).html')

def page_8(request):
    return render(request, 'pages/index (8).html')

def page_9(request):
    return render(request, 'pages/index (9).html')

def course_page_10(request):
    return render(request, 'pages/index (10).html')

def course_page_12(request):
    return render(request, 'pages/index (12).html')


