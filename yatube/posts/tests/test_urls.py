from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from http import HTTPStatus

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guest_client = Client()
        cls.author = User.objects.create_user(
            username='test_author'
        )
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(
            cls.author
        )
        cls.not_author = User.objects.create_user(
            username='test_not_author'
        )
        cls.authorized_client_not_author = Client()
        cls.authorized_client_not_author.force_login(
            cls.not_author
        )
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_text',
            author=cls.author,
            group=cls.group
        )
        cls.public_urls = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.author.username}/', 'posts/profile.html'),
            (f'/posts/{cls.post.pk}/', 'posts/post_detail.html'),
            ('/about/author/', 'about/author.html'),
            ('/about/tech/', 'about/tech.html')
        )
        cls.non_public_urls = (
            ('/create/', 'posts/create_post.html'),
            (f'/posts/{cls.post.pk}/edit/', 'posts/create_post.html')
        )
        return super().setUpClass()

    def test_public_urls_available_for_auth(self):
        """Публичный URL-адрес доступен авторизированному пользователю."""
        for url, _ in PostURLTests.public_urls:
            response = PostURLTests.authorized_client_author.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_public_urls_available_for_auth_not(self):
        """Публичный URL-адрес доступен неавторизированному пользователю."""
        for url, _ in PostURLTests.public_urls:
            response = PostURLTests.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_non_public_urls_available_for_auth(self):
        """Не публичный URL-адрес доступен авторизированному пользователю."""
        for url, _ in PostURLTests.non_public_urls:
            response = PostURLTests.authorized_client_author.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_post_edit_auth_not_author(self):
        """
        Кнопка (ссылка) для редактирования поста перенаправит
        авторизированного пользователя(не автора поста) на страницу поста.
        """
        response = PostURLTests.authorized_client_not_author.get(
            (f'/posts/{PostURLTests.post.pk}/edit/'),
            follow=True
        )
        self.assertRedirects(response,
                             (f'/posts/{PostURLTests.post.pk}/'))

    def test_404(self):
        """При запросе несуществующей страницы сервер возвращает код 404."""
        response = PostURLTests.guest_client.get('/posts/тест/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_public_urls_uses_correct_template(self):
        """Публичный URL-адрес использует соответствующий шаблон."""
        for url, template in PostURLTests.public_urls:
            response = PostURLTests.authorized_client_author.get(url)
            self.assertTemplateUsed(response, template)

    def test_non_public_urls_uses_correct_template(self):
        """Непубличный URL-адрес использует соответствующий шаблон."""
        for url, template in PostURLTests.non_public_urls:
            response = PostURLTests.authorized_client_author.get(url)
            self.assertTemplateUsed(response, template)

    def test_non_public_urls_edit_auth_not_author(self):
        """
        Запрос с непубличным URL-адресом направляет
        неавторизированного пользователя на страницу авторизации.
        """
        for url, _ in PostURLTests.non_public_urls:
            response = PostURLTests.guest_client.get(url)
            self.assertRedirects(
                response,
                '/auth/login/?next=' + url
            )
