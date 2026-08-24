from django.db.models import Avg, Count, Q, Sum
from core.models import Claim, CredibilityEvent, Evidence, UserTopicScore

def recalculate_user_topic_score(user, topic):
    """MVP score: Bayesian-ish prediction accuracy + community evidence usefulness.
    Keeps new users near 50 until enough resolved history exists.
    """
    predictions = Claim.objects.filter(author=user, topic=topic, kind=Claim.Kind.PREDICTION,
                                       status__in=[Claim.Status.VERIFIED, Claim.Status.FALSE])
    total = predictions.count()
    correct = predictions.filter(status=Claim.Status.VERIFIED).count()
    # Prior: 2 correct / 4 observations => starts at 50 and moves gradually.
    prediction_score = 100 * ((correct + 2) / (total + 4))

    ev = Evidence.objects.filter(submitted_by=user, claim__topic=topic).annotate(
        vote_sum=Sum('votes__value')
    )
    sums = [e.vote_sum or 0 for e in ev]
    evidence_rep = sum(sums) / max(len(sums), 1)
    evidence_component = max(0, min(100, 50 + evidence_rep * 5))

    score = round((prediction_score * 0.7) + (evidence_component * 0.3), 2)
    obj, _ = UserTopicScore.objects.update_or_create(user=user, topic=topic, defaults={
        'score': score, 'resolved_predictions': total, 'correct_predictions': correct,
        'evidence_reputation': round(evidence_rep, 2),
    })
    return obj

def resolve_prediction(claim, is_correct, note=''):
    if claim.kind != Claim.Kind.PREDICTION:
        raise ValueError('Only prediction claims can be resolved with this function.')
    claim.status = Claim.Status.VERIFIED if is_correct else Claim.Status.FALSE
    claim.resolution_note = note
    claim.save(update_fields=['status','resolution_note','updated_at'])
    score = recalculate_user_topic_score(claim.author, claim.topic)
    CredibilityEvent.objects.create(
        user=claim.author, topic=claim.topic, claim=claim,
        delta=5.0 if is_correct else -5.0,
        reason='Prediction resolved correct' if is_correct else 'Prediction resolved incorrect',
    )
    return score
