#LIBRARIES
from django.core.cache import cache

#BASICEDIT
from contentious.contrib.basicedit.models import ContentItem
from contentious.contrib.basicedit.utils import (
    content_dict_cache_key,
    get_cache_timeout,
)


class BasicEditAPI(object):
    """ Implementation of the ContentiousInterface for doing simple editing. """

    def in_edit_mode(self, context):
        """ Are we in edit mode?  At the moment we're assuming that all admin
            users are always in edit mode.  You might want to override this method.
        """
        return True
        try:
            user = context['request'].user
            return user.is_admin
        except (KeyError, AttributeError):
            return False

    def get_content_data(self, key, template_context):
        content_dict = self._get_content_dict(template_context) #that's a dict of dicts
        try:
            return content_dict[key]
        except KeyError:
            return {}

    def save_content_data(self, key, data, template_context):
        obj, created = ContentItem.objects.get_or_create(
            key=key,
            defaults=data
        )
        if not created:
            for key, value in data.items():
                setattr(obj, key, value)
            obj.save()
        self._clear_caches(template_context)

    def _get_content_dict(self, template_context):
        """ An efficient way for us to fetch content data without hitting the DB
            multiple times on the same request.  Tries to get the content by:
            1. getting it from a temporary cache on the request object, 2. getting
            it from memcache, 3. getting it from the database.
            Returns a dict of dicts.
        """
        request = template_context['request']
        #The first time we fetch the content on a given request we store it on the request object
        try:
            return request._content_cache_dict
        except AttributeError:
            pass
        cache_key = content_dict_cache_key()
        content_dict = cache.get(cache_key)
        if content_dict is None:
            content_objects = ContentItem.objects.all()
            content_dict = {obj.key: obj.content_dict for obj in content_objects}
            cache.set(cache_key, content_dict, get_cache_timeout())
        request._content_cache_dict = content_dict
        return content_dict

    def _clear_caches(self, template_context):
        """ Clear our caches from both the request object and memcache. """
        request = template_context['request']
        try:
            del request._content_cache_dict
        except AttributeError:
            pass
        cache.delete(content_dict_cache_key())
