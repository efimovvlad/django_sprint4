from django.shortcuts import render, get_object_or_404, redirect
from blog.models import Post, Category, User, Comment
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, ListView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import PostForm, CommentForm, UserForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count


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


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    queryset = search_params(Post.objects).annotate(
        comment_count=Count('comments'))
    ordering = ('-pub_date', 'title')
    paginate_by = 10


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


def edit_post(request, pk):
    template = 'blog/create.html'
    instance = get_object_or_404(Post, pk=pk)
    if instance.author != request.user:
        return redirect('blog:post_detail', pk=pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=instance
    )
    context = {'form': form}
    if form.is_valid():
        instance.save()
        return redirect('blog:post_detail', pk=pk)
    return render(request, template, context)


def post_detail(request, pk):
    template = 'blog/detail.html'
    instance = get_object_or_404(Post, pk=pk)
    filters = {}
    if instance.author != request.user:
        filters = {
            'is_published': True,
            'category__is_published': True,
            'pub_date__lte': timezone.now()
        }
    post = get_object_or_404(Post, pk=pk, **filters)
    form = CommentForm()
    comments = Comment.objects.filter(post_id=pk).order_by('created_at')
    context = {'form': form, 'post': post, 'comments': comments}
    return render(request, template, context)


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = search_params(Post.objects).filter(
        category=category
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date', 'title')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'category': category}
    return render(request, template, context)


def profile(request, username):
    template = 'blog/profile.html'
    profile = get_object_or_404(User, username=username)
    filters = {}
    if request.user.id != profile.id:
        filters = {
            'is_published': True,
            'category__is_published': True,
            'pub_date__lte': timezone.now()
        }
    posts = Post.objects.select_related(
        'category',
        'location',
        'author'
    ).filter(
        author_id=profile.id, **filters,
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date', 'title')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': profile,
        'page_obj': page_obj
    }
    return render(request, template, context)


def edit_profile(request):
    template = 'blog/user.html'
    profile = get_object_or_404(User, username=request.user.username)
    form = UserForm(request.POST or None, instance=profile)
    context = {'form': form}
    if form.is_valid():
        form.save()
        return redirect('blog:profile', request.user.username)
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', pk=post_id)


def edit_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    instance = get_object_or_404(Comment, pk=comment_id)
    if instance.author != request.user:
        return redirect('blog:post_detail', pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id)
    form = CommentForm(request.POST or None, instance=comment)
    context = {
        'form': form,
        'comment': comment
    }
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    return render(request, template, context)


def delete_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    instance = get_object_or_404(Comment, pk=comment_id)
    if instance.author != request.user:
        return redirect('blog:post_detail', pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id)
    context = {'comment': comment}
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id)
    return render(request, template, context)
