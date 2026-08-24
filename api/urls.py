from rest_framework.routers import DefaultRouter
from .views import TopicViewSet, ClaimViewSet, EvidenceViewSet, PositionViewSet, FollowViewSet, FeedViewSet, LeaderboardViewSet
router = DefaultRouter()
router.register('topics', TopicViewSet, basename='topic')
router.register('claims', ClaimViewSet, basename='claim')
router.register('evidence', EvidenceViewSet, basename='evidence')
router.register('positions', PositionViewSet, basename='position')
router.register('following', FollowViewSet, basename='following')
router.register('feed', FeedViewSet, basename='feed')
router.register('leaderboard', LeaderboardViewSet, basename='leaderboard')
urlpatterns = router.urls
