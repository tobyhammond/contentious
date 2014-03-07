# SYSTEM
import logging
import re

# LIBRARIES
from django import template
from django.template import loader, TemplateSyntaxError
from django.utils.html import escape

# CONTENTIOUS
from ..api import api
from ..constants import (
    SELF_CLOSING_HTML_TAGS,
    TREAT_CONTENT_AS_HTML_TAGS,
)

register = template.Library()


@register.tag
def editable(parser, token):
    """ Template tag which allows an HTML element to be editable.
        Allows editing of the contents of the tag and/or any of the attributes.
        Renders with a whole load of magic data-x attributes for edit mode, or
        just renders the tag 'normally' otherswise.  If the tag has not been
        edited (i.e. there's no object in the DB for it) then the default
        attributes specified in the tag are used along with the contents of the
        template tag as the contents of the HTML tag.
    """
    parts = token.split_contents()
    templ_tag_name = parts[0]
    html_tag_name = parts[1] #this cannot be a variable because we need to know what it is *now*
    key = parser.compile_filter(parts[2])
    kwargs = convert_kwarg_strings_to_kwargs(parts[3:], parser, templ_tag_name)

    try:
        editables = kwargs.pop("editable") #take out the list of editable things
    except KeyError:
        raise TemplateSyntaxError("%s tag expects an 'editable' kwarg." % templ_tag_name)

    optionals = kwargs.pop("optional", None)
    extra = kwargs.pop("extra", None) #take out the 'extra' info, if given
    #everything else remaining in kwargs should be the attributes for the HTML tag
    if html_tag_name in SELF_CLOSING_HTML_TAGS:
        nodelist = None
    else:
        nodelist = parser.parse(('endeditable',))
        parser.delete_first_token()

    return EditableTag(html_tag_name, key, editables, optionals, kwargs, nodelist, extra)


class EditableTag(template.Node):
    """ Node for the {% editable %}. """

    def __init__(self, tag_name, key, editables, optionals, attrs, nodelist, extra=None):
        self.tag_name = tag_name
        self.key = key
        self.editables = editables
        self.optionals = optionals
        self.attrs = attrs
        self.nodelist = nodelist
        self.extra = extra

    def render(self, context, is_nested=False):
        """ Render the HTML tag for the page.
            This will contain all of the edited items (attributes and content),
            with the defaults used for ones which have not been edited.  In
            edit mode we also add lots of data-x attributes for the JS.
        """
        #Note, we should not modifiy the properties of self in here, hence variables
        #from the context are resolved into new variables, not the properties
        key = self.key.resolve(context)
        attrs = {k: v.resolve(context) for k, v in self.attrs.items()}
        editables = self.editables.resolve(context)
        optionals = self.optionals.resolve(context) if self.optionals else []
        extra = self.extra.resolve(context) if self.extra else None

        assert not ('content' in editables and EditableTag in [type(t) for t in self.nodelist]), "Cannot edit content if editable contains nested editables"

        if isinstance(editables, basestring):
            #Allow editables to be passed in as either a comma-separated string or
            #an interable
            editables = [x for x in editables.split(",") if x]

        if isinstance(optionals, basestring):
            optionals = [x for x in optionals.split(",") if x]

        edit_mode = api.in_edit_mode(context)
        data = api.get_content_data(key, context).copy()
        data_was_provided = bool(data)

        #Check that the edited data only contains items which are allowed to be edited
        data = {k:v for k, v in data.items() if k in editables}
        #Now start to build the HTML tag...
        final_attrs = {}
        #start with the default attrs which were defined in the template tag
        final_attrs.update(attrs)

        if edit_mode:
            final_attrs.update({
                "data-cts-key": key,
                "data-cts-editables": ",".join(editables),
                "data-cts-optionals": ",".join(optionals)
            })
            if extra:
                final_attrs["data-cts-extra"] = extra
            #Add a CSS class, preserving any which is already defined
            classes = final_attrs.get("class", "").split(" ")
            classes.append("cts-nested-editable" if is_nested else "cts-editable")

            switched_off = data.pop('display', None) is False

            final_attrs['data-cts-switched-off'] = int(switched_off)
            if switched_off:
                classes.append("cts-switched-off")

            if not data_was_provided:
                classes.append("cts-default-data")

            #Add the key of the content as the id of the HTML tag if it doesn't already have one
            if "id" not in final_attrs:
                final_attrs["id"] = key

            final_attrs['class'] = " ".join(c for c in classes if c)
        elif data.pop('display', None) is False:
            # we aren't in edit mode and content is set to not show
            return ''

        #remove the content from the data dict, everything else is attrs
        content = data.pop('content', None)
        if self.is_self_closing():
            #We check that 'content' was NOT IN the data dict, rather than
            #just checking that it was in there but as an empty string
            assert content is None
            content = ""
        elif content is None:
            #'content' was not provided in the data dict, so use the default
            #contents of the template tag
            content = ""
            for tag in self.nodelist:
                content += tag.render(context, is_nested=True) if isinstance(tag, EditableTag) else tag.render(context)

        elif not self.content_is_html():
            #If the content has been edited but is not to be treated as HTML
            content = escape(content)
        #then override them with any which have been edited
        final_attrs.update(data)
        #escape our attribute values
        final_attrs = {k: escape(v) for k, v in final_attrs.items()}
        #Now start to build our tag
        assert not (content and self.is_self_closing())

        tag_spec = {
            "tag_name": self.tag_name,
            "attrs": final_attrs,
            "content": content,
        }
        meta = {
            "context": context,
            "key": key,
            "editables": editables,
            "optionals": optionals,
            "extra": extra,
            "in_edit_mode": edit_mode,
            "data_was_provided": data_was_provided,
        }
        tag_spec = self._pre_render(tag_spec, meta)
        tag = {
            "tag_name": tag_spec['tag_name'],
            "attrs": " ".join('%s%s' % (k, '="%s"' % v if v else '') for k, v in tag_spec['attrs'].items()),
            "self_close": " />" if self.is_self_closing() else ">",
            "content": tag_spec['content'],
            "close": "" if self.is_self_closing() else "</%s>" % tag_spec['tag_name'],
        }
        return "<%(tag_name)s %(attrs)s%(self_close)s%(content)s%(close)s" % tag


    def is_self_closing(self):
        return self.tag_name in SELF_CLOSING_HTML_TAGS

    def content_is_html(self):
        return self.tag_name in TREAT_CONTENT_AS_HTML_TAGS

    def _pre_render(self, tag_spec, meta):
        """ Give the API a chance to modify the data for the HTML tag before it's rendered. """
        try:
            pre_render = api.pre_render
        except AttributeError:
            return tag_spec
        return pre_render(tag_spec, meta)

    def _coerce_to_list(self, value):
        """ Given a value which can be either a comma-separated string or a list, return a list. """
        if isinstance(value, basestring):
            return value.split(",")
        return value


def convert_kwarg_strings_to_kwargs(kwarg_strings, parser, tag_name):
    """ Takes a list of strings from token.split_contents() which are in the format
        'some_key="some_value"' or 'some_key=variable_name' and returns a dict of
        the keys and values (with the values passed through compile_filter to allow)
        variables to be passed in with filters on them.
    """
    kwargs = {}
    for kwarg in kwarg_strings:
        try:
            if '=' not in kwarg:
                kwarg += '='
            idx = kwarg.index("=")
            key, value = kwarg[:idx], kwarg[idx+1:]
        except ValueError:
            raise TemplateSyntaxError("%s tag received non-kwarg: %s" % (tag_name, kwarg))
        value = parser.compile_filter(value)
        if key in kwargs:
            raise TemplateSyntaxError("%s tag received kwarg '%s' twice." % (tag_name, key))
        kwargs[key] = value
    return kwargs


@register.tag
def toolbar(parser, token):
    """
        Template tag that does or does not show the toolbar depending on
        the api.in_edit_mode()
    """
    parts = token.split_contents()

    templ_file_path = None
    if len(parts) == 2:
        templ_file_path = parts[1].strip('\"')
    elif len(parts) > 2:
        raise TemplateSyntaxError("%s tag expects either none or a single argument." % templ_tag_name)

    return ToolbarTag(templ_file_path)


class ToolbarTag(template.Node):
    """
        Tag only rendering the content (default or customised) if
        api.in_edit_mode() returns `False`
    """
    DEFAULT_TEMPL_PATH = "contentious/toolbar.html"

    def __init__(self, templ_file_path=None):
        self.templ_file_path = templ_file_path or self.DEFAULT_TEMPL_PATH

    def render(self, context):
        if not api.in_edit_mode(context):
            return ""

        t = loader.get_template(self.templ_file_path)
        self.nodelist = t.nodelist

        return self.nodelist.render(context)
