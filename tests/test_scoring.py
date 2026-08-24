from django.contrib.auth import get_user_model
from django.test import TestCase
from core.models import Topic, Claim
from core.services.scoring import recalculate_user_topic_score

class ScoringTests(TestCase):
    def test_new_user_starts_near_50(self):
        user = get_user_model().objects.create_user(username='alice', password='x')
        topic = Topic.objects.create(name='Economics', slug='economics')
        score = recalculate_user_topic_score(user, topic)
        self.assertEqual(score.score, 50.0)

    def test_correct_prediction_moves_score_up(self):
        user = get_user_model().objects.create_user(username='alice', password='x')
        topic = Topic.objects.create(name='Economics', slug='economics')
        Claim.objects.create(author=user, topic=topic, text='Inflation falls', kind='prediction', status='verified')
        score = recalculate_user_topic_score(user, topic)
        self.assertGreater(score.score, 50.0)
