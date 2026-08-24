from django.test import SimpleTestCase
from core.services.source_verification import UnsafeSourceURL, _quality, _validate_public_url

class SourceVerificationTests(SimpleTestCase):
    def test_private_local_url_is_blocked(self):
        with self.assertRaises(UnsafeSourceURL):
            _validate_public_url('http://127.0.0.1/private')

    def test_quality_is_provenance_not_truth_probability(self):
        score, reasons = _quality(
            url='https://example.com/a', title='Title', publisher='Example',
            published_at=object(), canonical='https://example.com/a', author='A')
        self.assertEqual(score, 1.0)
        self.assertIn('has_publication_date', reasons)
