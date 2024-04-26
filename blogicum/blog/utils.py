from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from django.urls import reverse
from .constants import FILTERS_FOR_PUBLIC
from .models import Comment
from .forms import CommentForm


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class CommentMixin(OnlyAuthorMixin):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'pk': self.kwargs['post_id']})


def search_params(posts, profile=None, filters=None):
    stage_1 = posts.select_related(
        'category',
        'location',
        'author'
    )
    if profile:
        stage_2 = stage_1.filter(author_id=profile, **filters)
    else:
        stage_2 = stage_1.filter(**FILTERS_FOR_PUBLIC)
    return stage_2.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date', 'title')
