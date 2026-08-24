from django.db.models import Count, Q
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Topic, Claim, Evidence, EvidenceVote, ClaimPosition, UserTopicScore, Follow
from core.services.scoring import resolve_prediction
from core.services.feed import ranked_feed
from .serializers import (
    TopicSerializer, ClaimSerializer, EvidenceSerializer, ClaimPositionSerializer,
    UserTopicScoreSerializer, FollowSerializer,
)

class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.all().order_by('name')
    serializer_class = TopicSerializer

class ClaimViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimSerializer
    def get_queryset(self):
        qs = Claim.objects.select_related('author','topic').annotate(evidence_count=Count('evidence'))
        topic = self.request.query_params.get('topic')
        status_ = self.request.query_params.get('status')
        kind = self.request.query_params.get('kind')
        q = self.request.query_params.get('q')
        if topic: qs = qs.filter(topic__slug=topic)
        if status_: qs = qs.filter(status=status_)
        if kind: qs = qs.filter(kind=kind)
        if q: qs = qs.filter(text__icontains=q)
        return qs
    def perform_create(self, serializer): serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'])
    def evidence(self, request, pk=None):
        qs = self.get_object().evidence.select_related('submitted_by').prefetch_related('votes')
        return Response(EvidenceSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def resolve(self, request, pk=None):
        claim = self.get_object()
        if claim.kind != Claim.Kind.PREDICTION:
            return Response({'detail':'Only predictions can be resolved.'}, status=400)
        is_correct = request.data.get('is_correct')
        if not isinstance(is_correct, bool):
            return Response({'detail':'is_correct must be true or false.'}, status=400)
        score = resolve_prediction(claim, is_correct=is_correct, note=request.data.get('note',''))
        return Response({'claim_id': claim.id, 'status': claim.status, 'new_topic_score': score.score})

class EvidenceViewSet(viewsets.ModelViewSet):
    serializer_class = EvidenceSerializer
    def get_queryset(self):
        return Evidence.objects.select_related('submitted_by','claim','claim__topic').prefetch_related('votes')
    def perform_create(self, serializer):
        evidence = serializer.save(submitted_by=self.request.user)
        if evidence.source_url:
            from core.tasks import verify_evidence_source
            try:
                verify_evidence_source.delay(evidence.pk)
            except Exception:
                pass

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def vote(self, request, pk=None):
        try: value = int(request.data.get('value', 0))
        except (TypeError, ValueError): value = 0
        if value not in (-1, 1): return Response({'detail':'value must be -1 or 1'}, status=400)
        EvidenceVote.objects.update_or_create(user=request.user, evidence=self.get_object(), defaults={'value':value})
        return Response({'ok': True, 'value': value})

class PositionViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimPositionSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self): return ClaimPosition.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        obj, _ = ClaimPosition.objects.update_or_create(
            user=self.request.user, claim=serializer.validated_data['claim'],
            defaults={'position':serializer.validated_data['position'],'confidence':serializer.validated_data.get('confidence',50)}
        )
        serializer.instance = obj

class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self): return Follow.objects.filter(follower=self.request.user).select_related('follower','following')
    def perform_create(self, serializer): serializer.save(follower=self.request.user)

class FeedViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        mode = request.query_params.get('mode', 'following')
        if mode not in {'global', 'following'}:
            mode = 'following'
        topic = request.query_params.get('topic', '')
        claims = ranked_feed(viewer=request.user, mode=mode, topic_slug=topic, limit=50)
        page = self.paginate_queryset(claims)
        if page is not None:
            serializer = ClaimSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        return Response(ClaimSerializer(claims, many=True, context={'request': request}).data)

    def get_queryset(self):
        # Router compatibility; ranked results are produced in list().
        return Claim.objects.none()

class LeaderboardViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = UserTopicScoreSerializer
    def get_queryset(self):
        qs = UserTopicScore.objects.select_related('user','topic')
        topic = self.request.query_params.get('topic')
        if topic: qs = qs.filter(topic__slug=topic)
        return qs.order_by('-score','-resolved_predictions')
