from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


@login_required
def post_create(request):
    """Создание нового поста, доступно авторизованному пользователю"""
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {'form': form}
    template = 'posts/create_post.html'
    if request.method == 'POST':
        if form.is_valid():
            text = form.cleaned_data['text']
            group = form.cleaned_data['group']
            image = form.cleaned_data['image']
            Post.objects.create(
                text=text, group=group, author=request.user, image=image
            )
            return redirect(f'/profile/{request.user.username}/')
        return render(request, template, context)
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    """Редактирование поста, доступно авторизованному автору поста"""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect(f'/posts/{post_id}/')
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {'form': form, 'is_edit': True}
    template = 'posts/create_post.html'
    if request.method == 'GET':
        return render(request, template, context)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect(f'/posts/{post_id}/')
        return render(request, template, context)
    return redirect(f'/posts/{post_id}/')


@login_required
def add_comment(request, post_id):
    """Добавление комментариев, доступно авторизованному пользователю"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def index(request):
    """Главная страница"""
    post_list = Post.objects.all()
    page_obj = create_page_obj(post_list, request)
    template = 'posts/index.html'
    context = {'page_obj': page_obj}
    return render(request, template, context)


def group_posts(request, slug):
    """Все посты выбранной группы"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = create_page_obj(posts, request)
    template = 'posts/group_list.html'
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Все посты выбранного автора"""
    user = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=user)
    page_obj = create_page_obj(post_list, request)
    following = Follow.objects.filter(user=request.user.id).filter(author=user)
    template = 'posts/profile.html'
    context = {
        'author': user,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Подробная информация о посте"""
    post = get_object_or_404(Post, id=post_id)
    template = 'posts/post_detail.html'
    form = CommentForm()
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


def create_page_obj(posts, request):
    """Пагинатор, создаваемый из листа постов"""
    paginator = Paginator(posts, settings.POSTS_IN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@login_required
def follow_index(request):
    """Страница постов авторов на которых подписан пользователь"""
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = create_page_obj(post_list, request)
    template = 'posts/follow.html'
    context = {'page_obj': page_obj}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Подписка пользователя на автора"""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка пользователя на автора"""
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
