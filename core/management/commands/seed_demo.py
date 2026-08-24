from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import (
    Claim,
    ClaimPosition,
    Evidence,
    EvidenceVote,
    Follow,
    Topic,
    UserTopicScore,
)


DEMO_USERS = [
    ("nadia_econ", "Nadia", "Economics"),
    ("omar_data", "Omar", "Technology"),
    ("salma_science", "Salma", "Science"),
    ("karim_policy", "Karim", "Politics"),
    ("lina_tech", "Lina", "Technology"),
    ("yusuf_world", "Yusuf", "World"),
]


DEMO_CLAIMS = [
    {
        "author": "nadia_econ",
        "topic": "economics",
        "text": "[DEMO] خفض زمن التنقل اليومي بنسبة 20% يرفع إنتاجية العاملين في المدن الكبيرة.",
        "kind": Claim.Kind.FACT,
        "status": Claim.Status.DISPUTED,
        "evidence": [
            (Evidence.Stance.SUPPORT, "تشير دراسة تجريبية افتراضية إلى ارتباط انخفاض زمن التنقل بتحسن الإنتاجية.", "Urban Mobility Lab", 0.86),
            (Evidence.Stance.CONTRADICT, "دراسة افتراضية أخرى ترى أن الأثر يختلف بشدة حسب نوع الوظيفة والعمل عن بعد.", "Work Patterns Institute", 0.78),
            (Evidence.Stance.CONTEXT, "البيانات التجريبية هنا مخصصة لعرض طريقة تنظيم الأدلة داخل Proof فقط.", "Proof Demo Dataset", 0.92),
        ],
    },
    {
        "author": "omar_data",
        "topic": "technology",
        "text": "[DEMO] An explainable ranking feed can reduce low-quality engagement bait without eliminating disagreement.",
        "kind": Claim.Kind.PREDICTION,
        "status": Claim.Status.OPEN,
        "evidence": [
            (Evidence.Stance.SUPPORT, "A synthetic A/B test shows higher evidence clicks when ranking reasons are visible.", "Demo Product Lab", 0.88),
            (Evidence.Stance.CONTRADICT, "A synthetic counter-study suggests explanation labels can themselves become engagement signals.", "Demo Systems Review", 0.72),
        ],
    },
    {
        "author": "salma_science",
        "topic": "science",
        "text": "[DEMO] عرض الأدلة المؤيدة والمعارضة في نفس الشاشة يساعد القارئ على اكتشاف نقاط عدم اليقين أسرع.",
        "kind": Claim.Kind.FACT,
        "status": Claim.Status.OPEN,
        "evidence": [
            (Evidence.Stance.SUPPORT, "تجربة واجهة افتراضية أظهرت زمنًا أقل للوصول إلى نقاط الخلاف الأساسية.", "Demo Cognitive Lab", 0.81),
            (Evidence.Stance.CONTEXT, "هذه ليست نتيجة علمية منشورة؛ هي بيانات توضيحية لتجربة الواجهة.", "Proof Demo Dataset", 0.94),
        ],
    },
    {
        "author": "karim_policy",
        "topic": "politics",
        "text": "[DEMO] Public policy discussions become more useful when claims are separated from evidence and opinion.",
        "kind": Claim.Kind.OPINION,
        "status": Claim.Status.OPEN,
        "evidence": [
            (Evidence.Stance.SUPPORT, "A synthetic moderation experiment found fewer circular arguments after separating evidence from opinion.", "Demo Civic Lab", 0.79),
            (Evidence.Stance.CONTRADICT, "A synthetic qualitative review found that rigid structure can discourage casual participation.", "Demo Community Review", 0.75),
        ],
    },
    {
        "author": "lina_tech",
        "topic": "technology",
        "text": "[DEMO] تقييم جودة توثيق المصدر يجب أن يكون منفصلًا عن الحكم على صحة محتواه.",
        "kind": Claim.Kind.FACT,
        "status": Claim.Status.VERIFIED,
        "evidence": [
            (Evidence.Stance.SUPPORT, "يمكن لمصدر أن يملك بيانات نشر واضحة وHTTPS ومع ذلك يحتوي على استنتاج خاطئ؛ لذلك القياسان مختلفان.", "Proof Design Notes", 0.91),
            (Evidence.Stance.CONTEXT, "درجة المصدر في Proof v0.5 تقيس provenance metadata فقط ولا تمثل fact-check.", "Proof Documentation", 0.97),
        ],
    },
    {
        "author": "yusuf_world",
        "topic": "world",
        "text": "[DEMO] A credibility score should be topic-specific rather than a single universal reputation number.",
        "kind": Claim.Kind.OPINION,
        "status": Claim.Status.OPEN,
        "evidence": [
            (Evidence.Stance.SUPPORT, "Synthetic user testing preferred separate expertise histories for economics, science, and technology.", "Demo Trust Lab", 0.84),
            (Evidence.Stance.CONTRADICT, "A synthetic usability test found that multiple scores may be harder for new users to understand.", "Demo UX Review", 0.76),
        ],
    },
    {
        "author": "nadia_econ",
        "topic": "business",
        "text": "[DEMO] الشركات التي توضح الافتراضات وراء توقعاتها المالية تقلل سوء الفهم مع المستثمرين.",
        "kind": Claim.Kind.FACT,
        "status": Claim.Status.OPEN,
        "evidence": [
            (Evidence.Stance.SUPPORT, "نموذج افتراضي لمذكرات استثمار أظهر عددًا أقل من أسئلة التوضيح عند إظهار الافتراضات.", "Demo Finance Lab", 0.82),
            (Evidence.Stance.CONTEXT, "النتيجة توضيحية وليست دراسة سوق حقيقية.", "Proof Demo Dataset", 0.93),
        ],
    },
    {
        "author": "salma_science",
        "topic": "health",
        "text": "[DEMO] Health claims require stronger evidence thresholds than casual lifestyle claims.",
        "kind": Claim.Kind.OPINION,
        "status": Claim.Status.OPEN,
        "evidence": [
            (Evidence.Stance.SUPPORT, "A synthetic risk model assigns higher evidence requirements where incorrect claims could cause greater harm.", "Demo Safety Lab", 0.89),
            (Evidence.Stance.CONTEXT, "This example exists only to demonstrate topic-sensitive discussion design.", "Proof Demo Dataset", 0.95),
        ],
    },
]


class Command(BaseCommand):
    help = "Load idempotent synthetic demo users, claims, evidence, votes, follows and credibility scores."

    def handle(self, *args, **options):
        User = get_user_model()

        required_topics = {item[2].lower() for item in DEMO_USERS}
        required_topics |= {item["topic"] for item in DEMO_CLAIMS}
        missing = [slug for slug in sorted(required_topics) if not Topic.objects.filter(slug=slug).exists()]
        if missing:
            self.stderr.write(
                self.style.ERROR(
                    "Missing topics: %s. Run `python manage.py seed_topics` first." % ", ".join(missing)
                )
            )
            return

        users = {}
        for username, first_name, _topic in DEMO_USERS:
            user, _created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first_name, "email": f"{username}@example.invalid"},
            )
            if not user.has_usable_password():
                pass
            else:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            users[username] = user

        # A small deterministic follow graph so the Following feed is not empty.
        follow_pairs = [
            ("nadia_econ", "omar_data"),
            ("nadia_econ", "salma_science"),
            ("omar_data", "lina_tech"),
            ("salma_science", "nadia_econ"),
            ("karim_policy", "yusuf_world"),
            ("lina_tech", "salma_science"),
            ("yusuf_world", "karim_policy"),
        ]
        for follower, following in follow_pairs:
            Follow.objects.get_or_create(follower=users[follower], following=users[following])

        created_claims = []
        for index, spec in enumerate(DEMO_CLAIMS, start=1):
            topic = Topic.objects.get(slug=spec["topic"])
            claim, _created = Claim.objects.get_or_create(
                author=users[spec["author"]],
                topic=topic,
                text=spec["text"],
                defaults={"kind": spec["kind"], "status": spec["status"]},
            )
            if claim.kind != spec["kind"] or claim.status != spec["status"]:
                claim.kind = spec["kind"]
                claim.status = spec["status"]
                claim.save(update_fields=["kind", "status", "updated_at"])
            created_claims.append(claim)

            for ev_index, (stance, note, publisher, quality) in enumerate(spec["evidence"], start=1):
                evidence, _created = Evidence.objects.get_or_create(
                    claim=claim,
                    submitted_by=users[spec["author"]],
                    stance=stance,
                    note=note,
                    defaults={
                        "source_url": f"https://example.com/proof-demo/{index}/{ev_index}",
                        "source_title": f"Synthetic demo source {index}.{ev_index}",
                        "source_publisher": publisher,
                        "source_domain": "example.com",
                        "source_verification_status": Evidence.VerificationStatus.CHECKED,
                        "source_quality_score": quality,
                        "source_quality_reasons": ["https", "has_title", "has_publisher", "has_publication_date"],
                    },
                )
                changed = False
                for field, value in {
                    "source_title": f"Synthetic demo source {index}.{ev_index}",
                    "source_publisher": publisher,
                    "source_domain": "example.com",
                    "source_verification_status": Evidence.VerificationStatus.CHECKED,
                    "source_quality_score": quality,
                    "source_quality_reasons": ["https", "has_title", "has_publisher", "has_publication_date"],
                }.items():
                    if getattr(evidence, field) != value:
                        setattr(evidence, field, value)
                        changed = True
                if changed:
                    evidence.save()

        # Community positions: intentionally mixed to make disagreement visible.
        position_cycle = [
            ClaimPosition.Position.TRUE,
            ClaimPosition.Position.UNSURE,
            ClaimPosition.Position.FALSE,
            ClaimPosition.Position.TRUE,
            ClaimPosition.Position.UNSURE,
            ClaimPosition.Position.TRUE,
        ]
        confidences = [82, 58, 71, 76, 55, 88]
        demo_user_list = list(users.values())
        for claim_index, claim in enumerate(created_claims):
            for user_index, user in enumerate(demo_user_list):
                position = position_cycle[(claim_index + user_index) % len(position_cycle)]
                confidence = confidences[(claim_index + user_index) % len(confidences)]
                ClaimPosition.objects.update_or_create(
                    user=user,
                    claim=claim,
                    defaults={"position": position, "confidence": confidence},
                )

        # Evidence usefulness votes create visible reputation and ranking signals.
        for claim_index, claim in enumerate(created_claims):
            for evidence_index, evidence in enumerate(claim.evidence.all()):
                for user_index, user in enumerate(demo_user_list):
                    value = EvidenceVote.Value.DOWN if (claim_index + evidence_index + user_index) % 7 == 0 else EvidenceVote.Value.UP
                    EvidenceVote.objects.update_or_create(
                        user=user,
                        evidence=evidence,
                        defaults={"value": value},
                    )

        # Topic-specific credibility values are deliberately different per user/topic.
        base_scores = {
            "nadia_econ": {"economics": 84, "business": 76},
            "omar_data": {"technology": 81},
            "salma_science": {"science": 88, "health": 79},
            "karim_policy": {"politics": 74},
            "lina_tech": {"technology": 86},
            "yusuf_world": {"world": 77},
        }
        for username, topic_scores in base_scores.items():
            for slug, score in topic_scores.items():
                UserTopicScore.objects.update_or_create(
                    user=users[username],
                    topic=Topic.objects.get(slug=slug),
                    defaults={
                        "score": score,
                        "resolved_predictions": 8,
                        "correct_predictions": max(1, round(8 * score / 100)),
                        "evidence_reputation": round((score - 50) / 10, 2),
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded Proof demo dataset: {len(users)} users, {len(created_claims)} claims, "
                f"{Evidence.objects.filter(claim__in=created_claims).count()} evidence items."
            )
        )
        self.stdout.write("All demo claims are synthetic and are marked with [DEMO].")
