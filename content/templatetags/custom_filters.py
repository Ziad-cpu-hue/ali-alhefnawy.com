from django import template

register = template.Library()

@register.filter
def get_dict_value(dictionary, key):
    return dictionary.get(key, "لم يتم الإجابة") if isinstance(dictionary, dict) else "لم يتم الإجابة"
