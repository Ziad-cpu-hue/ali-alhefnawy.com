from django import template

register = template.Library()

@register.filter
def get_dict_value(dictionary, key):
    return dictionary.get(key, "لم يتم الإجابة") if isinstance(dictionary, dict) else "لم يتم الإجابة"


@register.filter
def is_answer_correct(question, given_answer):
    """
    يحدد هل إجابة الطالب صحيحة (للأسئلة الاختيارية فقط).
    True / False = صحيحة أو خاطئة، None = سؤال مقالي بانتظار المراجعة اليدوية.
    """
    if question.question_type != "mcq":
        return None
    correct_choice = question.choices.filter(is_correct=True).first()
    if not correct_choice:
        return None
    return given_answer == correct_choice.text


@register.filter
def correct_choice_text(question):
    """يرجع نص الاختيار الصحيح لسؤال اختياري، أو None لغير ذلك."""
    if question.question_type != "mcq":
        return None
    correct_choice = question.choices.filter(is_correct=True).first()
    return correct_choice.text if correct_choice else None


@register.filter
def subtract(value, arg):
    """طرح بسيط يُستخدم في القوالب (مثال: عدد الأسئلة الخاطئة = الإجمالي - الصحيحة)."""
    try:
        return value - arg
    except (TypeError, ValueError):
        return ""

