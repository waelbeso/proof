from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ClaimForm, EvidenceForm, RegisterForm
from .models import Claim, ClaimPosition, EvidenceVote, Follow, Topic, UserTopicScore
from .ui import language_for
from .services.feed import ranked_feed


def _claim_queryset():
    return Claim.objects.select_related('author','topic').annotate(
        evidence_count=Count('evidence', distinct=True),
        support_count=Count('evidence', filter=Q(evidence__stance='support'), distinct=True),
        contradict_count=Count('evidence', filter=Q(evidence__stance='contradict'), distinct=True),
        context_count=Count('evidence', filter=Q(evidence__stance='context'), distinct=True),
        true_count=Count('positions', filter=Q(positions__position='true'), distinct=True),
        false_count=Count('positions', filter=Q(positions__position='false'), distinct=True),
        unsure_count=Count('positions', filter=Q(positions__position='unsure'), distinct=True),
    )


def home(request):
    feed_mode = request.GET.get('feed', 'global')
    if feed_mode not in {'global', 'following'}:
        feed_mode = 'global'
    topic_slug = request.GET.get('topic','')
    claims = ranked_feed(viewer=request.user, mode=feed_mode, topic_slug=topic_slug, limit=50)
    return render(request, 'core/home.html', {
        'claims': claims,
        'topics': Topic.objects.all().order_by('name'),
        'selected_topic': topic_slug,
        'feed_mode': feed_mode,
    })


def claim_detail(request, pk):
    claim = get_object_or_404(_claim_queryset(), pk=pk)
    evidence = claim.evidence.select_related('submitted_by').annotate(vote_score=Sum('votes__value')).order_by('-created_at')
    current_position = None
    user_votes = {}
    if request.user.is_authenticated:
        current_position = ClaimPosition.objects.filter(user=request.user, claim=claim).first()
        user_votes = dict(EvidenceVote.objects.filter(user=request.user, evidence__claim=claim).values_list('evidence_id','value'))
    for ev in evidence:
        ev.user_vote = user_votes.get(ev.id)
    return render(request, 'core/claim_detail.html', {'claim':claim, 'evidence_list':evidence, 'current_position':current_position})


@login_required
def claim_create(request):
    lang = language_for(request)
    form = ClaimForm(request.POST or None, lang=lang)
    if request.method == 'POST' and form.is_valid():
        claim = form.save(commit=False)
        claim.author = request.user
        claim.save()
        return redirect('claim_detail', pk=claim.pk)
    return render(request, 'core/form_page.html', {'form':form, 'page_title': 'ادعاء جديد' if lang=='ar' else 'New claim', 'submit_label':'نشر' if lang=='ar' else 'Publish'})


@login_required
def evidence_create(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    lang = language_for(request)
    form = EvidenceForm(request.POST or None, lang=lang)
    if request.method == 'POST' and form.is_valid():
        evidence = form.save(commit=False)
        evidence.claim = claim
        evidence.submitted_by = request.user
        evidence.save()
        if evidence.source_url:
            from .tasks import verify_evidence_source
            try:
                verify_evidence_source.delay(evidence.pk)
            except Exception:
                pass
        return redirect('claim_detail', pk=claim.pk)
    return render(request, 'core/form_page.html', {'form':form, 'page_title': 'إضافة دليل' if lang=='ar' else 'Add evidence', 'submit_label':'إرسال الدليل' if lang=='ar' else 'Submit evidence', 'claim':claim})


@login_required
@require_POST
def position_update(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    position = request.POST.get('position')
    try:
        confidence = max(0, min(100, int(request.POST.get('confidence', 50))))
    except ValueError:
        confidence = 50
    if position not in {'true','false','unsure'}:
        return HttpResponseBadRequest('Invalid position')
    ClaimPosition.objects.update_or_create(user=request.user, claim=claim, defaults={'position':position,'confidence':confidence})
    return redirect('claim_detail', pk=claim.pk)


@login_required
@require_POST
def evidence_vote(request, evidence_id):
    from .models import Evidence
    evidence = get_object_or_404(Evidence, pk=evidence_id)
    try:
        value = int(request.POST.get('value', 0))
    except ValueError:
        value = 0
    if value not in (-1, 1):
        return HttpResponseBadRequest('Invalid vote')
    EvidenceVote.objects.update_or_create(user=request.user, evidence=evidence, defaults={'value':value})
    return redirect('claim_detail', pk=evidence.claim_id)


def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    scores = UserTopicScore.objects.filter(user=profile_user).select_related('topic').order_by('-score')
    claims = _claim_queryset().filter(author=profile_user)[:20]
    is_following = request.user.is_authenticated and Follow.objects.filter(follower=request.user, following=profile_user).exists()
    return render(request, 'core/profile.html', {
        'profile_user':profile_user, 'scores':scores, 'claims':claims, 'is_following':is_following,
        'followers_count':Follow.objects.filter(following=profile_user).count(),
        'following_count':Follow.objects.filter(follower=profile_user).count(),
    })


@login_required
@require_POST
def follow_toggle(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return redirect('profile', username=username)
    edge = Follow.objects.filter(follower=request.user, following=target)
    if edge.exists(): edge.delete()
    else: Follow.objects.create(follower=request.user, following=target)
    return redirect('profile', username=username)


def leaderboard(request):
    topic_slug = request.GET.get('topic','')
    qs = UserTopicScore.objects.select_related('user','topic').order_by('-score','-resolved_predictions')
    if topic_slug: qs = qs.filter(topic__slug=topic_slug)
    return render(request, 'core/leaderboard.html', {
        'scores':qs[:100], 'topics':Topic.objects.all().order_by('name'), 'selected_topic':topic_slug,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    lang = language_for(request)
    form = RegisterForm(request.POST or None, lang=lang)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('home')
    return render(request, 'core/register.html', {'form':form})


def set_ui_language(request, lang):
    if lang not in {'ar','en'}:
        return HttpResponseBadRequest('Unsupported language')
    request.session['ui_lang'] = lang
    nxt = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('home')
    if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        nxt = reverse('home')
    return redirect(nxt)
