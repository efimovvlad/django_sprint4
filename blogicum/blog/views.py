from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Post, Category, User, Comment
from .forms import PostForm, UserForm, CommentForm
from .utils import OnlyAuthorMixin, CommentMixin, search_params
from .constants import NUMBER_OF_POSTS, FILTERS_FOR_PUBLIC


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    queryset = search_params(Post.objects)
    paginate_by = NUMBER_OF_POSTS


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
    if request.user != instance.author:
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
    if request.user != instance.author:
        filters = FILTERS_FOR_PUBLIC
    post = get_object_or_404(Post.objects.select_related(
        'category',
        'location',
        'author'
    ), pk=pk, **filters)
    form = CommentForm()
    comments = Comment.objects.filter(
        post_id=pk).select_related('author').order_by('created_at')
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
    )
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'category': category}
    return render(request, template, context)


def profile(request, username):
    template = 'blog/profile.html'
    profile = get_object_or_404(User, username=username)
    filters = {}
    if request.user != profile:
        filters = FILTERS_FOR_PUBLIC
    posts = search_params(Post.objects, profile.id, filters)
    paginator = Paginator(posts, NUMBER_OF_POSTS)
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


class CommentUpdateView(CommentMixin, UpdateView):
    pass


class CommentDeleteView(CommentMixin, DeleteView):
    pass
