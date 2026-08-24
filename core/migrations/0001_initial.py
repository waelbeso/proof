from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Topic', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('name', models.CharField(max_length=80, unique=True)),
            ('name_ar', models.CharField(blank=True, max_length=80)),
            ('slug', models.SlugField(max_length=90, unique=True)),
            ('description', models.TextField(blank=True)),
            ('description_ar', models.TextField(blank=True)),
        ]),
        migrations.CreateModel(name='Claim', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('text', models.TextField(max_length=4000)),
            ('kind', models.CharField(choices=[('fact','Factual claim'),('prediction','Prediction'),('opinion','Opinion')], default='fact', max_length=16)),
            ('status', models.CharField(choices=[('open','Open'),('verified','Verified'),('false','False'),('disputed','Disputed'),('unresolved','Unresolved')], default='open', max_length=16)),
            ('resolution_note', models.TextField(blank=True)),
            ('resolves_at', models.DateTimeField(blank=True, null=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),('updated_at', models.DateTimeField(auto_now=True)),
            ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='claims', to=settings.AUTH_USER_MODEL)),
            ('topic', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='claims', to='core.topic')),
        ], options={'ordering':['-created_at']}),
        migrations.CreateModel(name='Evidence', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('stance', models.CharField(choices=[('support','Supports'),('contradict','Contradicts'),('context','Context')], max_length=16)),
            ('source_url', models.URLField(blank=True, max_length=1000)),('note', models.TextField(max_length=4000)),
            ('source_title', models.CharField(blank=True, max_length=300)),('published_at', models.DateTimeField(blank=True, null=True)),
            ('ai_quality_score', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0),django.core.validators.MaxValueValidator(1)])),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('claim', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidence', to='core.claim')),
            ('submitted_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidence_submissions', to=settings.AUTH_USER_MODEL)),
        ], options={'ordering':['-created_at']}),
        migrations.CreateModel(name='EvidenceVote', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('value', models.SmallIntegerField(choices=[(-1,'Not useful'),(1,'Useful')])),('created_at', models.DateTimeField(auto_now_add=True)),
            ('evidence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='core.evidence')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='ClaimPosition', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('position', models.CharField(choices=[('true','True'),('false','False'),('unsure','Unsure')], max_length=8)),
            ('confidence', models.PositiveSmallIntegerField(default=50, validators=[django.core.validators.MinValueValidator(0),django.core.validators.MaxValueValidator(100)])),
            ('created_at', models.DateTimeField(auto_now_add=True)),('updated_at', models.DateTimeField(auto_now=True)),
            ('claim', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='positions', to='core.claim')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='UserTopicScore', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('score', models.FloatField(default=50.0, validators=[django.core.validators.MinValueValidator(0),django.core.validators.MaxValueValidator(100)])),
            ('resolved_predictions', models.PositiveIntegerField(default=0)),('correct_predictions', models.PositiveIntegerField(default=0)),('evidence_reputation', models.FloatField(default=0.0)),('updated_at', models.DateTimeField(auto_now=True)),
            ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.topic')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topic_scores', to=settings.AUTH_USER_MODEL)),
        ], options={'ordering':['-score']}),
        migrations.CreateModel(name='Follow', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),('created_at', models.DateTimeField(auto_now_add=True)),
            ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following_edges', to=settings.AUTH_USER_MODEL)),
            ('following', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follower_edges', to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='CredibilityEvent', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),('delta', models.FloatField()),('reason', models.CharField(max_length=250)),('created_at', models.DateTimeField(auto_now_add=True)),
            ('claim', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.claim')),
            ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.topic')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credibility_events', to=settings.AUTH_USER_MODEL)),
        ], options={'ordering':['-created_at']}),
        migrations.AddConstraint(model_name='evidencevote', constraint=models.UniqueConstraint(fields=('user','evidence'), name='unique_evidence_vote')),
        migrations.AddConstraint(model_name='claimposition', constraint=models.UniqueConstraint(fields=('user','claim'), name='unique_claim_position')),
        migrations.AddConstraint(model_name='usertopicscore', constraint=models.UniqueConstraint(fields=('user','topic'), name='unique_user_topic_score')),
        migrations.AddConstraint(model_name='follow', constraint=models.UniqueConstraint(fields=('follower','following'), name='unique_follow')),
        migrations.AddConstraint(model_name='follow', constraint=models.CheckConstraint(condition=~models.Q(follower=models.F('following')), name='prevent_self_follow')),
        migrations.AddIndex(model_name='claim', index=models.Index(fields=['topic','status','-created_at'], name='core_claim_topic_i_idx')),
        migrations.AddIndex(model_name='claim', index=models.Index(fields=['author','-created_at'], name='core_claim_author__idx')),
        migrations.AddIndex(model_name='evidence', index=models.Index(fields=['claim','stance','-created_at'], name='core_eviden_claim_i_idx')),
        migrations.AddIndex(model_name='follow', index=models.Index(fields=['follower','-created_at'], name='core_follow_followe_idx')),
        migrations.AddIndex(model_name='follow', index=models.Index(fields=['following','-created_at'], name='core_follow_followi_idx')),
    ]
