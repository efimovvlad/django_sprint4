from django.shortcuts import render, get_object_or_404
from blog.models import Post, Category
from django.utils import timezone
from blog.constants import NUMBER_OF_POSTS


def search_params(posts):
    return posts.select_related(
        'category',
        'location',
        'author'
    ).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    )


def index(request):
    template = 'blog/index.html'
    post_list = search_params(Post.objects)[:NUMBER_OF_POSTS]
    context = {'post_list': post_list}
    return render(request, template, context)


def post_detail(request, pk):
    template = 'blog/detail.html'
    post = get_object_or_404(
        search_params(Post.objects),
        pk=pk
    )
    context = {'post': post}
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = search_params(Post.objects).filter(
        category=category
    )
    context = {'post_list': post_list, 'category': category}
    return render(request, template, context)
