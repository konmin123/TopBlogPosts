from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group

User = get_user_model()


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

    def test_posts_pages_exists_guest_client(self):
        """Страницы сайта доступны любому пользователю."""
        url_status_dict = {
            '/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.FOUND,
            '/profile/IvanIvanov/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            '/follow/': HTTPStatus.FOUND,
            '/fake_url/': HTTPStatus.NOT_FOUND,
        }
        for url, status in url_status_dict.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_posts_pages_exists_authorized_client(self):
        """Страницы сайта доступны авторезованному пользователю."""
        url_status_dict = {
            '/posts/1/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            '/follow/': HTTPStatus.OK,
            '/fake_url/': HTTPStatus.NOT_FOUND,
        }
        for url, status in url_status_dict.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_post_url_redirect_anonymous_on_admin_login(self):
        """Страницы приложения перенаправят анонимного пользователя
        на страницу логина.
        """
        url_redirect_url_dict = {
            '/posts/1/edit/': '/auth/login/?next=/posts/1/edit/',
            '/create/': '/auth/login/?next=/create/',
            '/follow/': '/auth/login/?next=/follow/',
        }
        for url, redirect_url in url_redirect_url_dict.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect_url)

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        url_templates_dict = {
            '/': 'posts/index.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/profile/IvanIvanov/': 'posts/profile.html',
            '/group/test-slug/': 'posts/group_list.html',
        }
        for url, template in url_templates_dict.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
