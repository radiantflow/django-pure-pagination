import functools

from django.template.loader import render_to_string
from django.core.paginator import (Paginator as BasePaginator,
                                   Page as BasePage,
                                   InvalidPage,
                                   PageNotAnInteger,
                                   EmptyPage)

from . import settings


class PageRepresentation(int):
    def __new__(cls, x, querystring):
        obj = int.__new__(cls, x)
        obj.querystring = querystring
        return obj


def page_querystring(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if isinstance(result, int):
            querystring = self._other_page_querystring(result)
            return PageRepresentation(result, querystring)

        if isinstance(result, list):
            new_result = []
            for number in result:
                if isinstance(number, int):
                    querystring = self._other_page_querystring(number)
                    new_result.append(PageRepresentation(number, querystring))
                else:
                    new_result.append(number)
            return new_result
        return result

    return wrapper


class Page(BasePage):
    def __init__(self, object_list, number, paginator):
        super(Page, self).__init__(object_list, number, paginator)
        self.request = None
        if paginator.request:
            # Reason: I just want to perform this operation once, and not once per page
            self.base_queryset = self.paginator.request.GET.copy()
            self.base_queryset['page'] = 'page'
            self.base_queryset = self.base_queryset.urlencode().replace('%', '%%').replace('page=page', 'page=%s')
            self.request = paginator.request

        self.number = PageRepresentation(number, self._other_page_querystring(number))
        self.anchor = paginator.anchor

    def __repr__(self):
        return '<Page %s of %s>' % (self.number, self.paginator.num_pages)

    @property
    def next_page(self):
        return self.paginator.page(self.next_page_number())

    @property
    def previous_page(self):
        return self.paginator.page(self.previous_page_number())

    @page_querystring
    def next_page_number(self):
        return self.number + 1

    @page_querystring
    def previous_page_number(self):
        return self.number - 1

    @page_querystring
    def pages(self):
        if self.paginator.num_pages <= settings.MAX_PAGES_DISPLAYED:
            return list(range(1, self.paginator.num_pages + 1))
        result = []

        num_pages = self.paginator.num_pages
        max_pages = settings.MAX_PAGES_DISPLAYED
        margin_pages = settings.MARGIN_PAGES_DISPLAYED

        left_boundary = margin_pages
        right_boundary = num_pages - margin_pages

        remaining_pages = max_pages - (margin_pages * 2)

        left_index = self.number - (remaining_pages / 2)
        right_index = left_index + remaining_pages

        if left_index <= left_boundary:
            left_index = margin_pages + 1
        elif right_index >= right_boundary:
            left_index = right_boundary + 1 - remaining_pages

        for page in range(1, num_pages + 1):
            if page <= left_boundary:
                result.append(page)
                continue
            if page > right_boundary:
                result.append(page)
                continue
            if (page >= left_index) and (remaining_pages > 0):
                result.append(page)
                remaining_pages -= 1
                continue

            if result and result[-1]:
                result.append(None)

        return result

    def _other_page_querystring(self, page_number):
        """
        Returns a query string for the given page, preserving any
        GET parameters present.
        """
        if self.paginator.request:
            return self.base_queryset % page_number

        return 'page=%s' % page_number

    def render_pager(self):
        if self.paginator.num_pages > 1:
            return render_to_string('pure_pagination/pagination.html', {
                'current_page': self,
                'page_obj': self,  # Issue 9 https://github.com/jamespacileo/django-pure-pagination/issues/9
                                   # Use same naming conventions as Django
                'request': self.request
            })
        else:
            return ''

    def render(self):
        return self.render_pager()

class Paginator(BasePaginator):
    page_class = Page

    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, request=None, anchor=None):
        super(Paginator, self).__init__(object_list, per_page, orphans=orphans,
                                        allow_empty_first_page=allow_empty_first_page)

        self.request = request
        self.anchor = anchor

    @property
    def first_page(self):
        """Retrieve the first page"""
        return self.page(1)

    @property
    def last_page(self):
        """Retrieve the last page"""
        return self.page(self.num_pages)

    def page(self, number):
        """Returns a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page

        if top + self.orphans >= self.count:
            top = self.count

        return self.page_class(self.object_list[bottom:top], number, self)


QuerySetPaginator = Paginator  # For backwards-compatibility.
