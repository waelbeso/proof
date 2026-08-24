from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from core.models import Topic, Claim, Evidence

class WebSmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='strong-pass-123')
        self.topic = Topic.objects.create(name='Economics', name_ar='الاقتصاد', slug='economics')
        self.claim = Claim.objects.create(author=self.user, topic=self.topic, text='Inflation will fall.', kind='prediction')

    def test_home_and_arabic_default(self):
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'ادعاءات تستحق الفحص')
        self.assertContains(r, 'Inflation will fall.')
        self.assertContains(r, 'موجز مرتب بالدليل')

    def test_language_switch(self):
        self.client.get(reverse('set_ui_language', args=['en']))
        r = self.client.get(reverse('home'))
        self.assertContains(r, 'Claims worth examining')

    def test_claim_detail(self):
        r = self.client.get(reverse('claim_detail', args=[self.claim.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Inflation will fall.')
        self.assertContains(r, 'موجز مرتب بالدليل')
    def test_evidence_ux_bilingual_source_quality(self):
        Evidence.objects.create(
            claim=self.claim, submitted_by=self.user, stance='support',
            note='Official release supports the claim.', source_url='https://example.com/report',
            source_title='Official report', source_publisher='Example Publisher',
            source_domain='example.com', source_verification_status='checked',
            source_quality_score=0.8, source_quality_reasons=['https','has_title','has_publisher'],
        )
        r = self.client.get(reverse('claim_detail', args=[self.claim.pk]))
        self.assertContains(r, 'توازن الأدلة')
        self.assertContains(r, 'جودة توثيق المصدر')
        self.assertContains(r, '80%')
        self.client.get(reverse('set_ui_language', args=['en']))
        r = self.client.get(reverse('claim_detail', args=[self.claim.pk]))
        self.assertContains(r, 'Evidence balance')
        self.assertContains(r, 'Source provenance')
        self.assertContains(r, 'Strong')

