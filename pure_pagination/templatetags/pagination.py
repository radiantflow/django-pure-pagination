from copy import copy
from url_tools.helper import  UrlHelper
from django import template


register = template.Library()


@register.simple_tag
def pagination_link(page_obj, page, **kwargs):
    request_copy = copy(page_obj.request)
    if hasattr(request_copy, 'original_path'):
        request_copy.path = request_copy.original_path
    url = UrlHelper(request_copy.get_full_path())
    try:
        page = int(page)
        if page == 1:
            url.del_params('page', **kwargs)
        else:
            url.update_query_data(page=page, **kwargs)
        full_url = url.get_full_path()
        if page_obj.anchor:
            full_url += '#%s' % page_obj.anchor
        return full_url
    except:
        return ''
