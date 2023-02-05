import shutil
import tempfile
from django.contrib.auth import get_user_model
# from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings

from ..models import Post, Group, Comment, Follow

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
        cls.user_2 = User.objects.create_user(username='PetrPetrov')
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user_2)

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='test-description',
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый текст комментария',
            author=cls.user,
        )

        cls.follow = Follow.objects.create(
            user=cls.user_2,
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def check_post_field(self, post_from_context: Post):
        """Функция проверки полей объекта Post"""
        self.assertEqual(post_from_context.text, self.post.text)
        self.assertEqual(post_from_context.created, self.post.created)
        self.assertEqual(post_from_context.author, self.post.author)
        self.assertEqual(post_from_context.group, self.post.group)
        self.assertEqual(post_from_context.contact, self.post.contact)
        self.assertEqual(post_from_context.image, self.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}):
                'posts/post_detail.html',
            reverse('posts:post_detail', kwargs={'post_id': 2}):
                'core/404.html',
            reverse('posts:post_edit', kwargs={'post_id': 1}):
                'posts/create_post.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        post_form_context = response.context['page_obj'][0]
        self.check_post_field(post_form_context)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        post_form_context = response.context['page_obj'][0]
        self.check_post_field(post_form_context)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        post_form_context = response.context['page_obj'][0]
        self.check_post_field(post_form_context)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        post_from_context = response.context['post']
        self.check_post_field(post_from_context)
        post_comment = response.context['comments'][0]
        self.assertEqual(post_comment, self.comment)

    def test_post_create_pages_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:create_post')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_pages_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_paginator_correct_count_posts(self):
        """Страницы пагинатора содержат корректное количество постов."""
        for post in range(3):
            Post.objects.create(text='Тестовый текст',
                                author=self.user,
                                group=self.group,
                                )
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 3)
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_add_new_post_on_follower_index(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан"""
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        post_count_before = len(response.context['page_obj'])
        Post.objects.create(text='Тестовый текст',
                            author=self.user,
                            group=self.group,
                            )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        post_count_after = len(response.context['page_obj'])
        self.assertEqual(post_count_before + 1, post_count_after)

    def test_not_add_new_post_on_not_follower_index(self):
        """Новая запись пользователя не появляется в ленте тех, кто не
        подписан."""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post_count_before = len(response.context['page_obj'])
        Post.objects.create(text='Тестовый текст',
                            author=self.user_2,
                            group=self.group,
                            )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post_count_after = len(response.context['page_obj'])
        self.assertEqual(post_count_before, post_count_after)

    def test_correct_follow_object_fields(self):
        """Поля создоваемой подписки содержат корректные данные"""
        follow_object = Follow.objects.get(id=1)
        self.assertEqual(follow_object.user, self.follow.user)
        self.assertEqual(follow_object.author, self.follow.author)

    def test_profile_follow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей."""
        count_follow_obj_before = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': 'PetrPetrov'})
        )
        count_follow_obj_after = Follow.objects.count()
        self.assertEqual(count_follow_obj_after, count_follow_obj_before + 1)

    def test_profile_unfollow(self):
        """Авторизованный пользователь может удалять свои подписки."""
        count_follow_obj_before = Follow.objects.count()
        self.authorized_client_2.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': 'IvanIvanov'})
        )
        count_follow_obj_after = Follow.objects.count()
        self.assertEqual(count_follow_obj_after, count_follow_obj_before - 1)

    # def test_index_cache(self):
    #     """Кэширование страницы index.html работает корректно"""
    #     response = self.guest_client.get(reverse('posts:index'))
    #     Post.objects.get(id=1).delete()
    #     new_response = self.guest_client.get(reverse('posts:index'))
    #     self.assertEqual(response.content, new_response.content)
    #     cache.clear()
    #     new_response = self.guest_client.get(reverse('posts:index'))
    #     self.assertNotEqual(response.content, new_response.content)
