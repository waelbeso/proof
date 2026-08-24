from django.contrib.auth import views as auth_views
from django.urls import path
from . import web_views

urlpatterns = [
    path('', web_views.home, name='home'),
    path('claims/new/', web_views.claim_create, name='claim_create'),
    path('claims/<int:pk>/', web_views.claim_detail, name='claim_detail'),
    path('claims/<int:pk>/evidence/new/', web_views.evidence_create, name='evidence_create'),
    path('claims/<int:pk>/position/', web_views.position_update, name='position_update'),
    path('evidence/<int:evidence_id>/vote/', web_views.evidence_vote, name='evidence_vote'),
    path('u/<str:username>/', web_views.profile_view, name='profile'),
    path('u/<str:username>/follow/', web_views.follow_toggle, name='follow_toggle'),
    path('leaderboard/', web_views.leaderboard, name='leaderboard'),
    path('register/', web_views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('lang/<str:lang>/', web_views.set_ui_language, name='set_ui_language'),
]
