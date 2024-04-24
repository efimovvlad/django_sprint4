from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from .constants import FILTERS_FOR_PUBLIC


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


def search_params(posts, profile=None, guest=None):
    stage_1 = posts.select_related(
        'category',
        'location',
        'author'
    )
    if profile:
        if guest is True:
            filters = FILTERS_FOR_PUBLIC
        else:
            filters = {}
        stage_2 = stage_1.filter(
            author_id=profile, **filters,
        )
    else:
        stage_2 = stage_1.filter(
            **FILTERS_FOR_PUBLIC
        )
    return stage_2.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date', 'title')