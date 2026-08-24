from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class Topic(models.Model):
    name = models.CharField(max_length=80, unique=True)
    name_ar = models.CharField(max_length=80, blank=True)
    slug = models.SlugField(max_length=90, unique=True)
    description = models.TextField(blank=True)
    description_ar = models.TextField(blank=True)
    def __str__(self): return self.name

class Claim(models.Model):
    class Kind(models.TextChoices):
        FACT = 'fact', 'Factual claim'
        PREDICTION = 'prediction', 'Prediction'
        OPINION = 'opinion', 'Opinion'
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        VERIFIED = 'verified', 'Verified'
        FALSE = 'false', 'False'
        DISPUTED = 'disputed', 'Disputed'
        UNRESOLVED = 'unresolved', 'Unresolved'

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='claims')
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name='claims')
    text = models.TextField(max_length=4000)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.FACT)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    resolution_note = models.TextField(blank=True)
    resolves_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['topic','status','-created_at']), models.Index(fields=['author','-created_at'])]
    def __str__(self): return self.text[:80]

class Evidence(models.Model):
    class VerificationStatus(models.TextChoices):
        UNVERIFIED = 'unverified', 'Unverified'
        PENDING = 'pending', 'Pending'
        CHECKED = 'checked', 'Checked'
        FAILED = 'failed', 'Failed'
        BLOCKED = 'blocked', 'Blocked'

    class Stance(models.TextChoices):
        SUPPORT = 'support', 'Supports'
        CONTRADICT = 'contradict', 'Contradicts'
        CONTEXT = 'context', 'Context'
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='evidence')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evidence_submissions')
    stance = models.CharField(max_length=16, choices=Stance.choices)
    source_url = models.URLField(max_length=1000, blank=True)
    note = models.TextField(max_length=4000)
    source_title = models.CharField(max_length=300, blank=True)
    source_publisher = models.CharField(max_length=200, blank=True)
    source_domain = models.CharField(max_length=255, blank=True)
    source_verification_status = models.CharField(max_length=16, choices=VerificationStatus.choices, default=VerificationStatus.UNVERIFIED)
    source_checked_at = models.DateTimeField(null=True, blank=True)
    source_quality_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(1)])
    source_quality_reasons = models.JSONField(default=list, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    ai_quality_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['claim','stance','-created_at'])]

class EvidenceVote(models.Model):
    class Value(models.IntegerChoices):
        DOWN = -1, 'Not useful'
        UP = 1, 'Useful'
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='votes')
    value = models.SmallIntegerField(choices=Value.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','evidence'], name='unique_evidence_vote')]

class ClaimPosition(models.Model):
    class Position(models.TextChoices):
        TRUE = 'true', 'True'
        FALSE = 'false', 'False'
        UNSURE = 'unsure', 'Unsure'
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='positions')
    position = models.CharField(max_length=8, choices=Position.choices)
    confidence = models.PositiveSmallIntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','claim'], name='unique_claim_position')]

class UserTopicScore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topic_scores')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    score = models.FloatField(default=50.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    resolved_predictions = models.PositiveIntegerField(default=0)
    correct_predictions = models.PositiveIntegerField(default=0)
    evidence_reputation = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','topic'], name='unique_user_topic_score')]
        ordering = ['-score']


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following_edges')
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='follower_edges')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower','following'], name='unique_follow'),
            models.CheckConstraint(condition=~models.Q(follower=models.F('following')), name='prevent_self_follow'),
        ]
        indexes = [models.Index(fields=['follower','-created_at']), models.Index(fields=['following','-created_at'])]

class CredibilityEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='credibility_events')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    claim = models.ForeignKey(Claim, on_delete=models.SET_NULL, null=True, blank=True)
    delta = models.FloatField()
    reason = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
