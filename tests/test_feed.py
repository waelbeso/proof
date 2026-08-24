from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.models import Claim, ClaimPosition, Evidence, EvidenceVote, Follow, Topic, UserTopicScore
from core.services.feed import ranked_feed


class FeedRankingTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(username='viewer', password='x')
        self.alice = User.objects.create_user(username='alice', password='x')
        self.bob = User.objects.create_user(username='bob', password='x')
        self.carol = User.objects.create_user(username='carol', password='x')
        self.topic = Topic.objects.create(name='Economics', name_ar='الاقتصاد', slug='economics')

    def claim(self, author, text, hours_old=1, kind='fact'):
        c = Claim.objects.create(author=author, topic=self.topic, text=text, kind=kind)
        Claim.objects.filter(pk=c.pk).update(created_at=timezone.now() - timedelta(hours=hours_old))
        c.refresh_from_db()
        return c

    def add_quality_evidence(self, claim, submitter, stance='support', quality=0.9, votes=0):
        ev = Evidence.objects.create(
            claim=claim, submitted_by=submitter, stance=stance,
            note='Documented evidence', ai_quality_score=quality,
        )
        voters = []
        for i in range(votes):
            u = User.objects.create_user(username=f'v{claim.pk}_{stance}_{i}', password='x')
            EvidenceVote.objects.create(user=u, evidence=ev, value=1)
            voters.append(u)
        return ev

    def test_evidence_beats_empty_popularity(self):
        documented = self.claim(self.alice, 'Documented claim', hours_old=5)
        self.add_quality_evidence(documented, self.bob, 'support', 0.95, votes=2)
        self.add_quality_evidence(documented, self.carol, 'contradict', 0.90, votes=2)

        noisy = self.claim(self.bob, 'Popular but unsupported', hours_old=1)
        for i in range(12):
            u = User.objects.create_user(username=f'p{i}', password='x')
            ClaimPosition.objects.create(user=u, claim=noisy, position='true', confidence=90)

        feed = ranked_feed(viewer=self.viewer, mode='global', limit=10)
        ids = [c.id for c in feed]
        self.assertLess(ids.index(documented.id), ids.index(noisy.id))
        ranked = next(c for c in feed if c.id == documented.id)
        self.assertIn('strong_evidence', ranked.feed_reasons)
        self.assertIn('evidence_both_sides', ranked.feed_reasons)

    def test_missing_credibility_is_neutral_not_excluded(self):
        newcomer = self.claim(self.alice, 'Fresh newcomer claim', hours_old=2)
        veteran = self.claim(self.bob, 'Veteran claim', hours_old=2)
        UserTopicScore.objects.create(
            user=self.bob, topic=self.topic, score=95,
            resolved_predictions=25, correct_predictions=23,
        )
        self.add_quality_evidence(newcomer, self.carol, quality=0.9)
        feed = ranked_feed(viewer=self.viewer, mode='global', limit=10)
        n = next(c for c in feed if c.id == newcomer.id)
        self.assertIn('new_voice', n.feed_reasons)
        self.assertGreater(n.feed_score, 0)

    def test_following_feed_is_strict_membership(self):
        followed = self.claim(self.alice, 'Followed author')
        outside = self.claim(self.bob, 'Outside author')
        Follow.objects.create(follower=self.viewer, following=self.alice)
        feed = ranked_feed(viewer=self.viewer, mode='following', limit=10)
        ids = [c.id for c in feed]
        self.assertIn(followed.id, ids)
        self.assertNotIn(outside.id, ids)

    def test_diversity_reduces_author_monopoly(self):
        for i in range(5):
            c = self.claim(self.alice, f'Alice {i}', hours_old=i + 1)
            self.add_quality_evidence(c, self.carol, quality=0.95)
        other = self.claim(self.bob, 'Bob strong claim', hours_old=3)
        self.add_quality_evidence(other, self.carol, quality=0.9)

        feed = ranked_feed(viewer=self.viewer, mode='global', limit=6)
        first_four_authors = [c.author_id for c in feed[:4]]
        self.assertIn(self.bob.id, first_four_authors)
