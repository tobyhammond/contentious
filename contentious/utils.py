#STANDARD LIB
import json

#LIBRARIES
from django.http import HttpResponse
from django.utils.html import escape
from django.utils.safestring import SafeData


def json_response_from_exception(error):
    """ Given an exception instance (preferably a ValidationError) return an
        HTTP response with JSON giving the error(s).
    """
    try:
        errors_dict = error.message_dict
    except AttributeError:
        try:
            errors_dict = {'__all__': error.messages}
        except AttributeError:
            errors_dict = {'__all__': [unicode(error)]}
    return HttpResponse(
        safe_json_dump(errors_dict),
        content_type="application/json;charset=utf-8",
        status=400,
    )


def safe_json_dump(obj):
    """ A wrapper for json.dumps which first checks all strings to see if they
        are marked as HTML safe, and if not then escapes them before JSON-ifying.
    """
    obj = recursive_make_safe(obj)
    return json.dumps(obj)


def recursive_make_safe(obj):
    """ Given any object (usually a dict, list or tuple), recursively dig through
        it and make sure that all strings in it are HTML safe.  Dict keys are ignored.
    """
    if isinstance(obj, basestring) and not isinstance(obj, SafeData):
        return escape(obj)
    elif isinstance(obj, (list, tuple)):
            new = [] #don't modify the original while iterating over it
            for value in obj:
                new.append(recursive_make_safe(value))
    elif isinstance(obj, dict):
        new = {} #don't modify the original while iterating over it
        for key, value in obj.items():
            new[key] = recursive_make_safe(value)
    else:
        return obj
    return new

