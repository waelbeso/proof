from .ui import UI, language_for

def ui_context(request):
    lang = language_for(request)
    return {
        'UI_LANG': lang,
        'UI_DIR': 'rtl' if lang == 'ar' else 'ltr',
        't': UI[lang],
    }
