from celery import shared_task
from django.contrib.auth import get_user_model
from core.models import Topic
from core.services.scoring import recalculate_user_topic_score

@shared_task
def recalculate_score(user_id, topic_id):
    user = get_user_model().objects.get(pk=user_id)
    topic = Topic.objects.get(pk=topic_id)
    return recalculate_user_topic_score(user, topic).score


@shared_task(bind=True, autoretry_for=(TimeoutError,), retry_backoff=True, max_retries=2)
def verify_evidence_source(self, evidence_id):
    from django.utils import timezone
    from core.models import Evidence
    from core.services.source_verification import UnsafeSourceURL, inspect_source
    evidence = Evidence.objects.get(pk=evidence_id)
    if not evidence.source_url:
        return {'status': 'skipped'}
    evidence.source_verification_status = Evidence.VerificationStatus.PENDING
    evidence.save(update_fields=['source_verification_status'])
    try:
        result = inspect_source(evidence.source_url)
    except UnsafeSourceURL:
        evidence.source_verification_status = Evidence.VerificationStatus.BLOCKED
        evidence.source_checked_at = timezone.now()
        evidence.save(update_fields=['source_verification_status','source_checked_at'])
        return {'status': 'blocked'}
    except Exception as exc:
        evidence.source_verification_status = Evidence.VerificationStatus.FAILED
        evidence.source_checked_at = timezone.now()
        evidence.save(update_fields=['source_verification_status','source_checked_at'])
        return {'status': 'failed', 'error': str(exc)[:200]}

    evidence.source_url = result['final_url']
    evidence.source_domain = result['domain']
    evidence.source_publisher = result['publisher']
    if result['title']:
        evidence.source_title = result['title']
    if result['published_at']:
        evidence.published_at = result['published_at']
    evidence.source_quality_score = result['quality_score']
    # Keep v0.3 feed compatibility; this is provenance quality, not truth probability.
    evidence.ai_quality_score = result['quality_score']
    evidence.source_quality_reasons = result['quality_reasons']
    evidence.source_verification_status = Evidence.VerificationStatus.CHECKED
    evidence.source_checked_at = timezone.now()
    evidence.save(update_fields=['source_url','source_domain','source_publisher','source_title','published_at','source_quality_score','ai_quality_score','source_quality_reasons','source_verification_status','source_checked_at'])
    return {'status': 'checked', 'quality_score': result['quality_score']}
