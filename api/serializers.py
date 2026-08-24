from django.contrib.auth import get_user_model
from rest_framework import serializers
from core.models import Topic, Claim, Evidence, EvidenceVote, ClaimPosition, UserTopicScore, Follow
User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username']

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id','name','name_ar','slug','description','description_ar']

class EvidenceSerializer(serializers.ModelSerializer):
    submitted_by = UserMiniSerializer(read_only=True)
    vote_score = serializers.SerializerMethodField()
    class Meta:
        model = Evidence
        fields = ['id','claim','submitted_by','stance','source_url','source_title','source_publisher','source_domain','source_verification_status','source_checked_at','source_quality_score','source_quality_reasons','note','published_at','ai_quality_score','vote_score','created_at']
        read_only_fields = ['submitted_by','source_publisher','source_domain','source_verification_status','source_checked_at','source_quality_score','source_quality_reasons','ai_quality_score']
    def get_vote_score(self, obj):
        return sum(obj.votes.values_list('value', flat=True))

class ClaimSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)
    evidence_count = serializers.SerializerMethodField()
    feed_score = serializers.SerializerMethodField()
    feed_reasons = serializers.SerializerMethodField()
    class Meta:
        model = Claim
        fields = ['id','author','topic','text','kind','status','resolution_note','resolves_at','evidence_count','feed_score','feed_reasons','created_at','updated_at']
        read_only_fields = ['author','status','resolution_note','feed_score','feed_reasons']
    def get_evidence_count(self, obj):
        return getattr(obj, 'evidence_count', None) if getattr(obj, 'evidence_count', None) is not None else obj.evidence.count()
    def get_feed_score(self, obj):
        return getattr(obj, 'feed_score', None)
    def get_feed_reasons(self, obj):
        return getattr(obj, 'feed_reasons', [])

class ClaimPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimPosition
        fields = ['id','claim','position','confidence','created_at','updated_at']

class UserTopicScoreSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    topic = TopicSerializer(read_only=True)
    class Meta:
        model = UserTopicScore
        fields = ['user','topic','score','resolved_predictions','correct_predictions','evidence_reputation','updated_at']

class FollowSerializer(serializers.ModelSerializer):
    follower = UserMiniSerializer(read_only=True)
    following_username = serializers.CharField(source='following.username', read_only=True)
    class Meta:
        model = Follow
        fields = ['id','follower','following','following_username','created_at']
        read_only_fields = ['follower']
