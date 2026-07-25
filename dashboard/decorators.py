from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def staff_required(view_func):
    """
    يسمح فقط للمستخدمين الذين قاموا بتسجيل الدخول ولديهم صلاحية is_staff
    (أي المعلم / الأدمن) بالوصول لصفحات لوحة التحكم الجديدة.
    أي شخص آخر يتم تحويله تلقائيًا لصفحة تسجيل الدخول الخاصة باللوحة.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, "الرجاء تسجيل الدخول للوصول إلى لوحة التحكم.")
            return redirect('dashboard:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
