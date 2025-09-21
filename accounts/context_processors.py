# accounts/context_processors.py
from accounts.models import Student
def student_session(request):
    """
    يضيف للمجال context: is_registered, student_name, student (لو موجود)
    يعمل في كل القوالب بعد تفعيله في settings.py
    """
    is_registered = request.session.get("is_registered", False)
    student_name = request.session.get("student_name", None)
    student_obj = None
    student_id = request.session.get("student_id")
    if student_id:
        try:
            student_obj = Student.objects.filter(id=student_id).first()
        except Exception:
            student_obj = None
    return {
        "is_registered": is_registered,
        "student_name": student_name,
        "student": student_obj,
    }
