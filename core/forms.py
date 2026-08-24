from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Claim, Evidence, Topic
from .ui import UI

User = get_user_model()

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username',)

    def __init__(self, *args, lang='ar', **kwargs):
        super().__init__(*args, **kwargs)
        t = UI[lang]
        self.fields['username'].label = t['username']
        self.fields['password1'].label = t['password']
        self.fields['password2'].label = t['password_confirm']
        for field in self.fields.values():
            field.help_text = ''
            field.widget.attrs.update({'class':'input'})

class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ('text','topic','kind','resolves_at')
        widgets = {
            'text': forms.Textarea(attrs={'rows':5, 'maxlength':4000}),
            'resolves_at': forms.DateTimeInput(attrs={'type':'datetime-local'}),
        }

    def __init__(self, *args, lang='ar', **kwargs):
        super().__init__(*args, **kwargs)
        self._lang = lang
        t = UI[lang]
        self.fields['text'].label = t['claim_text']
        self.fields['topic'].label = t['topic']
        self.fields['kind'].label = t['type']
        self.fields['resolves_at'].label = t['resolution_date']
        self.fields['topic'].queryset = Topic.objects.all().order_by('name')
        self.fields['resolves_at'].required = False
        kind_choices = [('fact', t['fact']), ('prediction', t['prediction']), ('opinion', t['opinion'])]
        self.fields['kind'].choices = kind_choices
        for field in self.fields.values():
            field.widget.attrs.update({'class':'input'})

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('kind') == Claim.Kind.PREDICTION and not cleaned.get('resolves_at'):
            self.add_error('resolves_at', 'Required for predictions.' if self.lang == 'en' else 'مطلوب للتوقعات.')
        return cleaned

    @property
    def lang(self):
        return getattr(self, '_lang', 'ar')

class EvidenceForm(forms.ModelForm):
    class Meta:
        model = Evidence
        fields = ('stance','source_url','source_title','note','published_at')
        widgets = {
            'note': forms.Textarea(attrs={'rows':4}),
            'published_at': forms.DateTimeInput(attrs={'type':'datetime-local'}),
        }

    def __init__(self, *args, lang='ar', **kwargs):
        super().__init__(*args, **kwargs)
        t = UI[lang]
        self.fields['stance'].label = t['stance']
        self.fields['stance'].choices = [('support',t['supports']),('contradict',t['contradicts']),('context',t['context'])]
        self.fields['source_url'].label = t['source_url']
        self.fields['source_title'].label = t['source_title']
        self.fields['note'].label = t['note']
        self.fields['published_at'].label = t['published_at']
        self.fields['published_at'].required = False
        self.fields['source_title'].required = False
        for field in self.fields.values():
            field.widget.attrs.update({'class':'input'})
