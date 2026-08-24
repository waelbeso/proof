from django.contrib import admin
from .models import Topic, Claim, Evidence, EvidenceVote, ClaimPosition, UserTopicScore, Follow, CredibilityEvent

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name','name_ar','slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('id','author','topic','kind','status','created_at')
    list_filter = ('kind','status','topic')
    search_fields = ('text','author__username')

@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('id','claim','submitted_by','stance','source_domain','source_verification_status','source_quality_score','created_at')
    list_filter = ('stance','source_verification_status')
    search_fields = ('source_url','source_title','source_publisher','note')

admin.site.register(EvidenceVote)
admin.site.register(ClaimPosition)
admin.site.register(UserTopicScore)
admin.site.register(Follow)
admin.site.register(CredibilityEvent)
