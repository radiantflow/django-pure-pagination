from copy import copy
from url_tools.helper import  UrlHelper
from django import template


register = template.Library()


@register.simple_tag
def pagination_link(request, page, **kwargs):
    request_copy = copy(request)
    if request_copy.original_path:
        request_copy.path = request_copy.original_path
    url = UrlHelper(request_copy.get_full_path())
    try:
        page = int(page)
        if page == 1:
            url.del_params('page', **kwargs)
        else:
            url.update_query_data(page=page, **kwargs)
        return url.get_full_path()
    except:
        return ''
