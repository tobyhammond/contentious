from django.conf import settings

def content_dict_cache_key(language):
    prefix = getattr(settings, "CONTENT_CACHE_PREFIX", "")
    return "%scontent_dict_cache_%s" % (prefix, language)

def get_cache_timeout():
    return getattr(settings, "CONTENT_CACHE_TIMEOUT", None)
