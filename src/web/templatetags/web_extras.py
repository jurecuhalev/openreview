from django import template

register = template.Library()


@register.simple_tag
def current_tab_class(url_name, name_to_match):
    if url_name.startswith(name_to_match):
        return "current"
    return ""
