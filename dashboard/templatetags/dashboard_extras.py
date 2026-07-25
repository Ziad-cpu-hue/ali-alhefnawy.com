from django import template

register = template.Library()


@register.filter
def get_attr(obj, field_name):
    """
    يقرأ أي حقل بالاسم من أي موديل ديناميكيًا، ويحوّل:
    - حقول الاختيارات (choices) إلى النص المعروض (get_FIELD_display)
    - علاقات ManyToMany إلى قائمة نصية مفصولة بفواصل
    - القيم الفارغة إلى "—"
    مستخدم في جدول العرض العام (generic_list.html) عشان نقدر نعرض أي عمود
    من غير ما نكتب كود مخصص لكل موديل.
    """
    if obj is None:
        return "—"

    display_method = getattr(obj, f'get_{field_name}_display', None)
    if callable(display_method):
        try:
            value = display_method()
            return value if value not in (None, '') else "—"
        except Exception:
            pass

    try:
        value = getattr(obj, field_name)
    except AttributeError:
        return "—"

    if callable(value):
        try:
            value = value()
        except Exception:
            return "—"

    if hasattr(value, 'all') and callable(getattr(value, 'all', None)):
        try:
            items = [str(x) for x in value.all()]
            return ", ".join(items) if items else "—"
        except Exception:
            return "—"

    if value in (None, ''):
        return "—"

    return value
