from django.core.management.base import BaseCommand
from core.models import Topic

TOPICS = [
    ('Economics','الاقتصاد','economics'),
    ('Technology','التكنولوجيا','technology'),
    ('Science','العلوم','science'),
    ('Business','الأعمال','business'),
    ('Politics','السياسة','politics'),
    ('Health','الصحة','health'),
    ('Sports','الرياضة','sports'),
    ('World','العالم','world'),
]

class Command(BaseCommand):
    help = 'Create the default bilingual Proof topics.'
    def handle(self, *args, **options):
        for name, name_ar, slug in TOPICS:
            Topic.objects.update_or_create(slug=slug, defaults={'name':name,'name_ar':name_ar})
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(TOPICS)} bilingual topics.'))
