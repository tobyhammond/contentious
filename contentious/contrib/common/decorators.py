#LIBRARIES
from django.http import HttpResponseForbidden
from django.template import RequestContext

#CONTENTIOUS
from contentious.api import api


def require_edit_mode(function):
    """ View function decorator for requiring api.in_edit_mode to be True. """
    def replacement(request, *args, **kwargs):
        context = RequestContext(request)
        if not api.in_edit_mode(context):
            return HttpResponseForbidden()
        return function(request, *args, **kwargs)
    return replacement
