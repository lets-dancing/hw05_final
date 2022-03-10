from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()

FIRST_PAGE_RECORDS = 10
SECOND_PAGE_RECORDS = 3
ALL_RECORDS_ON_PAGES = FIRST_PAGE_RECORDS + SECOND_PAGE_RECORDS


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.guest_client = Client()
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.templates_for_paginator = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.author.username}/', 'posts/profile.html'),
        )

    def test_paginator(self):
        posts = [Post(
            group=PaginatorViewsTest.group,
            text='test_post',
            author=PaginatorViewsTest.author)
            for i in range(ALL_RECORDS_ON_PAGES)
        ]
        Post.objects.bulk_create(posts)
        pages = (
            (1, FIRST_PAGE_RECORDS),
            (2, SECOND_PAGE_RECORDS),
        )
        for url, _ in PaginatorViewsTest.templates_for_paginator:
            with self.subTest(template=_):
                for page, count in pages:
                    response = PaginatorViewsTest.guest_client.get(
                        url, {'page': page}
                    )
                    self.assertEqual(
                        len(response.context['page_obj'].object_list),
                        count
                    )
