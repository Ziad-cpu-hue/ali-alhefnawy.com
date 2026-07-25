from django.shortcuts import render, get_object_or_404
from content.models import Card
from content.models import LectureContent, ExamContent  # إضافة ExamContent

def card_detail(request, card_id):
    # جلب بيانات الكارد من math_mastery
    card = get_object_or_404(Card, id=card_id)

    # تنظيم المحاضرات حسب الأسابيع من content
    lectures = LectureContent.objects.filter(course=card).order_by('week')
    exams = ExamContent.objects.filter(course=card).order_by('week')

    # تنظيم المحاضرات والامتحانات حسب الأسابيع
    content_by_week = {}

    for lecture in lectures:
        content_by_week.setdefault(lecture.week, []).append(lecture)

    for exam in exams:
        content_by_week.setdefault(exam.week, []).append(exam)

    context = {
        "card": card,  # إرسال الكارد بشكل ديناميكي
        "content_by_week": content_by_week,  # يحتوي على المحاضرات والامتحانات مرتبة حسب الأسابيع
    }

    return render(request, 'pages/index (12).html', context)
