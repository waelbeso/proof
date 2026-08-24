from django import template
register = template.Library()

LABELS = {
    'kind': {
        'en': {'fact':'Factual claim','prediction':'Prediction','opinion':'Opinion'},
        'ar': {'fact':'ادعاء واقعي','prediction':'توقع','opinion':'رأي'},
    },
    'status': {
        'en': {'open':'Open','verified':'Verified','false':'False','disputed':'Disputed','unresolved':'Unresolved'},
        'ar': {'open':'مفتوح','verified':'متحقق','false':'خاطئ','disputed':'محل نزاع','unresolved':'غير محسوم'},
    },
    'stance': {
        'en': {'support':'Supports','contradict':'Contradicts','context':'Context'},
        'ar': {'support':'يؤيد','contradict':'يناقض','context':'سياق'},
    },
    'position': {
        'en': {'true':'True','false':'False','unsure':'Unsure'},
        'ar': {'true':'صحيح','false':'خطأ','unsure':'غير متأكد'},
    },
    'feed_reason': {
        'en': {
            'strong_evidence':'Strong evidence', 'evidence_both_sides':'Evidence on both sides',
            'fresh':'Fresh', 'topic_credibility':'Credible in this topic',
            'useful_disagreement':'Useful disagreement', 'followed_author':'You follow this author',
            'new_voice':'New voice', 'worth_examining':'Worth examining',
        },
        'ar': {
            'strong_evidence':'أدلة قوية', 'evidence_both_sides':'أدلة من الجانبين',
            'fresh':'حديث', 'topic_credibility':'مصداقية في هذا المجال',
            'useful_disagreement':'خلاف مفيد', 'followed_author':'أنت تتابع الكاتب',
            'new_voice':'صوت جديد', 'worth_examining':'يستحق الفحص',
        },
    },
}

def _label(group, value, lang):
    return LABELS.get(group, {}).get(lang, {}).get(value, value)

@register.filter
def kind_label(value, lang='ar'): return _label('kind', value, lang)
@register.filter
def status_label(value, lang='ar'): return _label('status', value, lang)
@register.filter
def stance_label(value, lang='ar'): return _label('stance', value, lang)
@register.filter
def position_label(value, lang='ar'): return _label('position', value, lang)
@register.filter
def feed_reason_label(value, lang='ar'): return _label('feed_reason', value, lang)
@register.filter
def topic_name(topic, lang='ar'):
    if lang == 'ar' and getattr(topic, 'name_ar', ''):
        return topic.name_ar
    return topic.name


@register.filter
def source_status_label(value, lang='ar'):
    labels = {
        'ar': {'unverified':'غير مفحوص','pending':'جارٍ الفحص','checked':'تم فحص المصدر','failed':'تعذر الفحص','blocked':'رابط محظور'},
        'en': {'unverified':'Unverified','pending':'Checking','checked':'Source checked','failed':'Check failed','blocked':'Blocked URL'},
    }
    return labels.get(lang, labels['ar']).get(value, value)

@register.filter
def source_reason_label(value, lang='ar'):
    labels = {
        'ar': {'https':'HTTPS','http_only':'HTTP فقط','has_title':'عنوان واضح','has_publisher':'ناشر محدد','has_publication_date':'تاريخ نشر','has_canonical':'رابط أصلي','has_author_metadata':'بيانات مؤلف'},
        'en': {'https':'HTTPS','http_only':'HTTP only','has_title':'Clear title','has_publisher':'Named publisher','has_publication_date':'Publication date','has_canonical':'Canonical URL','has_author_metadata':'Author metadata'},
    }
    return labels.get(lang, labels['ar']).get(value, value)


@register.filter
def source_quality_percent(value):
    if value is None:
        return None
    try:
        return max(0, min(100, round(float(value) * 100)))
    except (TypeError, ValueError):
        return None

@register.filter
def source_quality_band(value, lang='ar'):
    if value is None:
        return ''
    try:
        score = float(value)
    except (TypeError, ValueError):
        return ''
    bands = {
        'ar': ('محدودة', 'متوسطة', 'قوية'),
        'en': ('Limited', 'Moderate', 'Strong'),
    }
    low, mid, high = bands.get(lang, bands['ar'])
    if score >= 0.75:
        return high
    if score >= 0.5:
        return mid
    return low
