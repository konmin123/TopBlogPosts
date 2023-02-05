import tempfile
from http import HTTPStatus
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..models import Post, Group, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='IvanIvanov')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='test-description',
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый текст комментария',
            author=cls.user,
        )

    def test_post_create(self):
        """Объект Post создаётся через форму"""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Текст из формы',
            'slug': 'test-slug',
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_comment_create_authorized_client(self):
        """Объект Comment создаётся через форму, авторизованным клиентом"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_comment_not_create_guest_client(self):
        """Объект Comment Не создаётся через форму, гостевым клиентом"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_post_edit(self):
        """Объект Post изменяется через форму"""
        form_data = {
            'text': 'Текст через форму',
            'slug': 'test-slug',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        changed_post = Post.objects.get(id=1)
        text_from_form = form_data['text']
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(changed_post.text, text_from_form)

    def test_add_user(self):
        """Объект User добавляется через форму"""
        form_data = {
            'first_name': 'TestName',
            'last_name': 'TestLastName',
            'username': 'User2',
            'email': 'test2@mail.ru',
            'password1': 'TestTest123',
            'password2': 'TestTest123',
        }
        count_users = User.objects.count()
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), count_users + 1)
