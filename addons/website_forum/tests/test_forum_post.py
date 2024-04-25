from odoo.addons.website_forum.tests.common import TestForumCommon


class TestForumPost(TestForumCommon):

    def forum_tags(self, user, forum, size=10):
        return self.env['forum.tag'].with_user(user).create([
            {
                'name': f'tag_{i}',
                'forum_id': forum.id,
            }
            for i in range(size)
        ])

    def test_get_related_posts(self):
        """Test the method returns 5 related posts based on tag similarity"""
        # Create forum posts and associate them tags
        forum_tags = self.forum_tags(self.user_admin, self.forum)
        forum_posts = self.env['forum.post'].with_user(self.user_admin).create(
            [
                {
                    'content': 'A post ...',
                    'forum_id': self.forum.id,
                    'name': 'Post...',
                    'tag_ids': forum_tags[:i]
                }
                for i in range(len(forum_tags) + 1)  # 11 posts with 0 to 10 tags
            ]
        )
        # First post (not tags), should return None
        self.assertEqual(forum_posts[0]._get_related_posts(), None)
        # Second post, most similar posts should be the 5 following posts
        self.assertEqual(forum_posts[1]._get_related_posts(), forum_posts[2:7])
        # Last post, most similar posts should be the 5 preceding posts in descending order
        self.assertEqual(forum_posts[-1]._get_related_posts(),
                            forum_posts[len(forum_posts) - 6: -1].sorted(reverse=True))
        # A post with a uniq tag, should return an empty record set
        self.assertEqual(len(self.post._get_related_posts()), 0)
