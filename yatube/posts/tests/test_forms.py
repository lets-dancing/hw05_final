import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Comment, Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.author = User.objects.create_user(username='testauthor')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.small_gif_old1 = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded_old1 = SimpleUploadedFile(
            name='small_old1.gif',
            content=cls.small_gif_old1,
            content_type='image/gif'
        )
        cls.group_old = Group.objects.create(
            title='test_group_old',
            slug='test-slug-old',
            description='test_description'
        )
        cls.group_new = Group.objects.create(
            title='test_group_new',
            slug='test-slug-new',
            description='test_description'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Проверка формы создания нового поста."""
        posts_count = Post.objects.count()
        group_field = PostFormTests.group_old.id
        form_data = {
            'text': 'test_new_post',
            'group': group_field,
            'image': PostFormTests.uploaded_old1
        }
        response = PostFormTests.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=1)
        post_image = form_data['image']
        self.assertRedirects(response, reverse('posts:profile',
                             args=[PostFormTests.author.username]))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.author, PostFormTests.author)
        self.assertEqual(post.group, PostFormTests.group_old)
        self.assertEqual(post.text, 'test_new_post')
        self.assertEqual(post_image, PostFormTests.uploaded_old1)

    def test_create_post_not_auth_user(self):
        """
        Проверка формы создания нового
        поста неавторизированным пользователем.
        """
        self.guest_client = Client()
        posts_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create')
        )
        self.assertRedirects(response, '/auth/login/?next=%2Fcreate%2F')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post(self):
        """
        Проверка формы редактирования поста и изменение
        его в базе данных.
        """
        post = Post.objects.create(
            text='test_post',
            group=PostFormTests.group_old,
            author=PostFormTests.author
        )
        group_field_new = PostFormTests.group_new.id
        form_data = {
            'text': 'test_edit_post',
            'group': group_field_new
        }
        response = PostFormTests.author_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': post.pk}
                    )
        )
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group_new.id,
                text='test_edit_post'
            ).exists()
        )
        self.assertFalse(
            Post.objects.filter(
                group=PostFormTests.group_old.id,
                text=post.text
            ).exists()
        )

    def test_post_comment(self):
        """Проверка создания нового комментария."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            author=PostFormTests.author
        )
        self.url = reverse('posts:add_comment', kwargs={'post_id': post.pk})
        response = PostFormTests.author_client.post(self.url)
        Comment.objects.create(
            post=post,
            author=PostFormTests.author,
            text='test_comment'
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': post.pk}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
