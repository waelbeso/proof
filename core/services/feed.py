"""Evidence-first feed ranking for Proof.

The goal is deliberately different from an engagement feed:
- evidence quality and diversity matter more than raw reactions;
- topic credibility helps, but is capped so established users cannot own the feed;
- constructive disagreement is rewarded only when a claim has evidence;
- freshness decays smoothly;
- repeated authors/topics receive diversity penalties during reranking;
- low-history authors receive a small exploration boost while a claim is fresh.

The service attaches ``feed_score``, ``feed_components`` and ``feed_reasons``
to Claim instances. No schema migration is required.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, log1p, log
from typing import Iterable

from django.db.models import Avg, Count, Q, Sum, OuterRef, Subquery, Value, IntegerField, FloatField
from django.db.models.functions import Coalesce
from django.utils import timezone

from core.models import Claim, Evidence, EvidenceVote, Follow, UserTopicScore


@dataclass(frozen=True)
class FeedConfig:
    candidate_limit: int = 300
    output_limit: int = 50
    freshness_half_life_hours: float = 48.0
    new_author_window_hours: float = 72.0
    new_author_prediction_threshold: int = 3
    author_repeat_penalty: float = 0.065
    topic_repeat_penalty: float = 0.030


CONFIG = FeedConfig()


def annotated_claims():
    """Base queryset with the bounded aggregate signals used by ranking.

    Vote sums and average evidence quality use correlated subqueries to avoid
    cartesian multiplication when evidence and positions are joined together.
    """
    vote_totals = EvidenceVote.objects.filter(evidence__claim=OuterRef('pk')).values('evidence__claim').annotate(
        total=Sum('value'),
        n=Count('id'),
    )
    quality = Evidence.objects.filter(claim=OuterRef('pk'), ai_quality_score__isnull=False).values('claim').annotate(
        avg=Avg('ai_quality_score')
    )
    return Claim.objects.select_related('author', 'topic').annotate(
        evidence_count=Count('evidence', distinct=True),
        support_count=Count('evidence', filter=Q(evidence__stance='support'), distinct=True),
        contradict_count=Count('evidence', filter=Q(evidence__stance='contradict'), distinct=True),
        context_count=Count('evidence', filter=Q(evidence__stance='context'), distinct=True),
        true_count=Count('positions', filter=Q(positions__position='true'), distinct=True),
        false_count=Count('positions', filter=Q(positions__position='false'), distinct=True),
        unsure_count=Count('positions', filter=Q(positions__position='unsure'), distinct=True),
        position_count=Count('positions', distinct=True),
        evidence_vote_count=Coalesce(Subquery(vote_totals.values('n')[:1], output_field=IntegerField()), Value(0)),
        evidence_vote_score=Coalesce(Subquery(vote_totals.values('total')[:1], output_field=IntegerField()), Value(0)),
        avg_ai_quality=Subquery(quality.values('avg')[:1], output_field=FloatField()),
    )


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _freshness(age_hours: float, half_life: float) -> float:
    if age_hours <= 0:
        return 1.0
    return 2 ** (-age_hours / half_life)


def _evidence_score(claim) -> tuple[float, float]:
    count = int(getattr(claim, 'evidence_count', 0) or 0)
    if count == 0:
        return 0.0, 0.0

    coverage = 1.0 - exp(-count / 2.4)
    quality = float(claim.avg_ai_quality) if claim.avg_ai_quality is not None else 0.50

    support = int(getattr(claim, 'support_count', 0) or 0)
    contradict = int(getattr(claim, 'contradict_count', 0) or 0)
    adversarial = 0.0
    if support and contradict:
        adversarial = (2.0 * min(support, contradict)) / max(1, support + contradict)

    vote_count = int(getattr(claim, 'evidence_vote_count', 0) or 0)
    vote_sum = int(getattr(claim, 'evidence_vote_score', 0) or 0)
    if vote_count:
        # Bayesian-ish shrinkage toward neutral: one small voting brigade cannot dominate.
        vote_quality = 0.5 + (vote_sum / (vote_count + 4.0)) * 0.5
    else:
        vote_quality = 0.5

    score = 0.45 * coverage + 0.25 * _clamp(quality) + 0.20 * adversarial + 0.10 * _clamp(vote_quality)
    return _clamp(score), adversarial


def _position_entropy(claim) -> float:
    counts = [
        int(getattr(claim, 'true_count', 0) or 0),
        int(getattr(claim, 'false_count', 0) or 0),
        int(getattr(claim, 'unsure_count', 0) or 0),
    ]
    total = sum(counts)
    if total < 2:
        return 0.0
    entropy = 0.0
    for c in counts:
        if c:
            p = c / total
            entropy -= p * log(p)
    return _clamp(entropy / log(3))


def _engagement_quality(claim) -> float:
    # Deliberately logarithmic and capped: 10,000 reactions are not 1,000x better than 10.
    activity = int(getattr(claim, 'position_count', 0) or 0) + int(getattr(claim, 'evidence_vote_count', 0) or 0)
    return _clamp(log1p(activity) / log(21))


def _credibility_value(raw_score: float | None) -> float:
    # Missing history is neutral, not punished. Compress extremes toward the middle.
    if raw_score is None:
        return 0.50
    normalized = _clamp(float(raw_score) / 100.0)
    return 0.50 + (normalized - 0.50) * 0.70


def _status_multiplier(status: str) -> float:
    return {
        Claim.Status.OPEN: 1.00,
        Claim.Status.DISPUTED: 1.02,
        Claim.Status.UNRESOLVED: 0.90,
        Claim.Status.VERIFIED: 0.82,
        Claim.Status.FALSE: 0.82,
    }.get(status, 1.0)


def _kind_multiplier(kind: str) -> float:
    return {
        Claim.Kind.FACT: 1.00,
        Claim.Kind.PREDICTION: 1.03,
        Claim.Kind.OPINION: 0.72,
    }.get(kind, 1.0)


def _score_claim(claim, *, now, following_ids: set[int], viewer_id: int | None, credibility_map: dict[tuple[int, int], tuple[float, int]], config: FeedConfig):
    age_hours = max(0.0, (now - claim.created_at).total_seconds() / 3600.0)
    freshness = _freshness(age_hours, config.freshness_half_life_hours)
    evidence, adversarial = _evidence_score(claim)
    entropy = _position_entropy(claim)
    disagreement = entropy * (0.35 + 0.65 * evidence)  # disagreement without evidence is mostly noise
    engagement = _engagement_quality(claim)

    raw_cred, history = credibility_map.get((claim.author_id, claim.topic_id), (50.0, 0))
    credibility = _credibility_value(raw_cred)

    relationship = 0.0
    if claim.author_id in following_ids:
        relationship += 0.10
    if viewer_id and claim.author_id == viewer_id:
        relationship += 0.025

    exploration = 0.0
    if history < config.new_author_prediction_threshold and age_hours <= config.new_author_window_hours:
        exploration = 0.045

    base = (
        0.30 * evidence
        + 0.21 * freshness
        + 0.16 * credibility
        + 0.13 * disagreement
        + 0.10 * engagement
        + relationship
        + exploration
    )
    final = _clamp(base * _status_multiplier(claim.status) * _kind_multiplier(claim.kind), 0.0, 1.20)

    reasons: list[str] = []
    if evidence >= 0.62:
        reasons.append('strong_evidence')
    if adversarial >= 0.45:
        reasons.append('evidence_both_sides')
    if freshness >= 0.66:
        reasons.append('fresh')
    if credibility >= 0.67 and history >= 3:
        reasons.append('topic_credibility')
    if disagreement >= 0.55:
        reasons.append('useful_disagreement')
    if claim.author_id in following_ids:
        reasons.append('followed_author')
    if exploration > 0:
        reasons.append('new_voice')
    if not reasons:
        reasons.append('worth_examining')

    claim.feed_score = round(final, 4)
    claim.feed_components = {
        'evidence': round(evidence, 4),
        'freshness': round(freshness, 4),
        'credibility': round(credibility, 4),
        'disagreement': round(disagreement, 4),
        'engagement': round(engagement, 4),
        'relationship': round(relationship, 4),
        'exploration': round(exploration, 4),
    }
    claim.feed_reasons = reasons[:3]
    return claim


def _diversity_rerank(items: Iterable, *, limit: int, topic_locked: bool, config: FeedConfig):
    pool = list(items)
    selected = []
    author_seen: dict[int, int] = {}
    topic_seen: dict[int, int] = {}

    while pool and len(selected) < limit:
        best_index = 0
        best_utility = float('-inf')
        for idx, claim in enumerate(pool):
            a_seen = author_seen.get(claim.author_id, 0)
            t_seen = topic_seen.get(claim.topic_id, 0)
            penalty = config.author_repeat_penalty * a_seen
            if not topic_locked:
                penalty += config.topic_repeat_penalty * t_seen
            if a_seen >= 2:
                penalty += 0.09 * (a_seen - 1)
            if not topic_locked and t_seen >= 3:
                penalty += 0.05 * (t_seen - 2)
            utility = claim.feed_score - penalty
            if utility > best_utility:
                best_utility = utility
                best_index = idx

        claim = pool.pop(best_index)
        claim.feed_rank_score = round(best_utility, 4)
        selected.append(claim)
        author_seen[claim.author_id] = author_seen.get(claim.author_id, 0) + 1
        topic_seen[claim.topic_id] = topic_seen.get(claim.topic_id, 0) + 1

    return selected


def ranked_feed(*, viewer=None, mode: str = 'global', topic_slug: str = '', limit: int | None = None, config: FeedConfig = CONFIG):
    """Return ranked Claim objects for the web/API feed.

    ``following`` remains a strict following feed. Ranking changes order, not membership.
    ``global`` is evidence-first discovery across the network.
    """
    limit = limit or config.output_limit
    qs = annotated_claims()

    viewer_id = getattr(viewer, 'id', None) if viewer and getattr(viewer, 'is_authenticated', False) else None
    following_ids: set[int] = set()
    if viewer_id:
        following_ids = set(Follow.objects.filter(follower_id=viewer_id).values_list('following_id', flat=True))

    if mode == 'following':
        if not viewer_id:
            return []
        if following_ids:
            qs = qs.filter(Q(author_id=viewer_id) | Q(author_id__in=following_ids))
        else:
            return []

    if topic_slug:
        qs = qs.filter(topic__slug=topic_slug)

    # Pull only a recent candidate window; Python performs transparent bounded scoring.
    candidates = list(qs.order_by('-created_at')[:config.candidate_limit])
    if not candidates:
        return []

    pairs = {(c.author_id, c.topic_id) for c in candidates}
    author_ids = {a for a, _ in pairs}
    topic_ids = {t for _, t in pairs}
    credibility_map = {
        (s.user_id, s.topic_id): (float(s.score), int(s.resolved_predictions))
        for s in UserTopicScore.objects.filter(user_id__in=author_ids, topic_id__in=topic_ids)
    }

    now = timezone.now()
    scored = [
        _score_claim(
            claim,
            now=now,
            following_ids=following_ids,
            viewer_id=viewer_id,
            credibility_map=credibility_map,
            config=config,
        )
        for claim in candidates
    ]
    scored.sort(key=lambda c: (c.feed_score, c.created_at), reverse=True)
    return _diversity_rerank(scored, limit=limit, topic_locked=bool(topic_slug), config=config)
