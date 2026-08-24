from django.db import migrations, models
import django.core.validators

class Migration(migrations.Migration):
    dependencies = [('core','0001_initial')]
    operations = [
        migrations.AddField(model_name='evidence', name='source_publisher', field=models.CharField(blank=True,max_length=200)),
        migrations.AddField(model_name='evidence', name='source_domain', field=models.CharField(blank=True,max_length=255)),
        migrations.AddField(model_name='evidence', name='source_verification_status', field=models.CharField(choices=[('unverified','Unverified'),('pending','Pending'),('checked','Checked'),('failed','Failed'),('blocked','Blocked')],default='unverified',max_length=16)),
        migrations.AddField(model_name='evidence', name='source_checked_at', field=models.DateTimeField(blank=True,null=True)),
        migrations.AddField(model_name='evidence', name='source_quality_score', field=models.FloatField(blank=True,null=True,validators=[django.core.validators.MinValueValidator(0),django.core.validators.MaxValueValidator(1)])),
        migrations.AddField(model_name='evidence', name='source_quality_reasons', field=models.JSONField(blank=True,default=list)),
    ]
