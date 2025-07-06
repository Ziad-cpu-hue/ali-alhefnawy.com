from django.http import JsonResponse 
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student
from django.contrib.auth.hashers import check_password, make_password

def register_student(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone_number = request.POST.get("phone_number")
        parent_phone_number = request.POST.get("parent_phone_number")
        grade = request.POST.get("grade")
        governorate = request.POST.get("governorate")
        password = request.POST.get("password")  # استقبال كلمة المرور

        # طباعة البيانات للتحقق
        print(f"First Name: {first_name}")
        print(f"Last Name: {last_name}")
        print(f"Phone Number: {phone_number}")
        print(f"Parent Phone Number: {parent_phone_number}")
        print(f"Grade: {grade}")
        print(f"Governorate: {governorate}")

        # التحقق من صحة البيانات
        if not all([first_name, last_name, phone_number, grade, governorate, password]):
            return JsonResponse({"success": False, "message": "يرجى ملء جميع الحقول المطلوبة."})

        try:
            student = Student.objects.create(
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                parent_phone_number=parent_phone_number,
                grade=grade,
                governorate=governorate,
                password=make_password(password)
            )
            student.save()

            # تخزين بيانات الطالب في الجلسة
            request.session["student_id"] = student.id
            request.session["student_name"] = f"{student.first_name} {student.last_name}"
            request.session["is_registered"] = True

            messages.success(request, "تم إنشاء الحساب بنجاح!")
            return JsonResponse({"success": True, "message": "تم إنشاء الحساب بنجاح!"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return render(request, "pages/register.html")

def home(request):
    # استرجاع بيانات الجلسة
    student_name = request.session.get("student_name", None)
    is_registered = request.session.get("is_registered", False)

    return render(request, 'pages/index (1).html', {
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






from django.shortcuts import render, get_object_or_404
from .models import Subscription


def course_page(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('login')  # تأكد من تسجيل الدخول

    subscriptions = Subscription.objects.filter(student=user)
    allowed_courses = [sub.course for sub in subscriptions]
    lectures_by_week = {}  # منطق جمع المحاضرات حسب الأسابيع

    return render(request, 'pages/index (4).html', {
        'allowed_courses': allowed_courses,
        'lectures_by_week': lectures_by_week,
    })



from django.http import HttpResponseForbidden

def protected_video(request, video_id):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden("Access Denied")

    video = get_object_or_404(Video, id=video_id)  # افترض أن لديك نموذج فيديو
    if not Subscription.objects.filter(student=user, course=video.course).exists():
        return HttpResponseForbidden("Access Denied")

    # قدم الفيديو إذا كان لديه الصلاحية
    return redirect(video.url)









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


#########################################################################################

import random
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from content.models import Course            # استيراد الموديل من التطبيق الصحيح
from .models import PaymentRequest
from .forms import FullPaymentForm

@login_required
def submit_payment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'GET':
        frac = random.randint(1, 999)
        # استخدام الحقل الصحيح price بدل base_price
        amount = course.price + Decimal(frac) / Decimal(1000)
        request.session['pending_amount'] = str(amount)
        form = FullPaymentForm(initial={'course': course})
        return render(request, 'Test/activation.html', {
            'form': form,
            'amount': amount,
            'platform_phone': '0109738599',
        })

    form = FullPaymentForm(request.POST, request.FILES)
    if form.is_valid():
        pr = form.save(commit=False)
        pr.student = request.user
        pr.amount_required = Decimal(request.session.pop('pending_amount'))
        pr.save()
        return redirect('accounts:payment_pending')
    amount = Decimal(request.session.get('pending_amount', course.price))
    return render(request, 'Test/activation.html', {
        'form': form,
        'amount': amount,
        'platform_phone': '0109738599',
    })



from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def payment_pending(request):
    return render(request, 'Test/payment_pending.html')
