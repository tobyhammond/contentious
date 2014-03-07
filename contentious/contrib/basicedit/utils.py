from django.conf import settings

def content_dict_cache_key():
    prefix = getattr(settings, "CONTENT_CACHE_PREFIX", "")
    return "%scontent_dict_cache" % prefix

def get_cache_timeout():
    return getattr(settings, "CONTENT_CACHE_TIMEOUT", None)
