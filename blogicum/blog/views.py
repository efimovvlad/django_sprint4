from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from blog.models import Post, Category, User, Comment
from .forms import PostForm, UserForm, CommentForm
from .utils import OnlyAuthorMixin, search_params
from .constants import NUMBER_OF_POSTS


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
    )
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'category': category}
    return render(request, template, context)


def profile(request, username):
    template = 'blog/profile.html'
    profile = get_object_or_404(User, username=username)
    guest = False
    if request.user.id != profile.id:
        guest = True
    posts = search_params(Post.objects, profile.id, guest)
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


def update_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if '/edit_comment/' in request.path:
        context = {
            'form': form,
            'comment': comment
        }
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id)
        return render(request, template, context)
    else:
        context = {'comment': comment}
        if request.method == 'POST':
            comment.delete()
            return redirect('blog:post_detail', post_id)
        return render(request, template, context)
