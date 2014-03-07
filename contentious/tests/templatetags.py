#SYSTEM
import re

#LIBRARIES
from django.template import Context, Template
from django.test import TestCase
from django.utils.html import escape
import mock

#CONTENTIOUS
from contentious.tests.mocks import (
    ConfigurableAPI,
    EditModeNoOpAPI,
    NoOpAPI,
)

no_op_api = NoOpAPI()
edit_mode_no_op_api = EditModeNoOpAPI()
configurable_api = ConfigurableAPI()


class EditableTagTest(TestCase):
    """ Tests for the contentious template tag(s). """

    templ = Template(
        '{% load contentious %}'
        '{% editable div "my_key" editable="content,title" optional="title" title=variable onclick="boogie()" %}'
        'Default content'
        '{% endeditable %}'
    )
    p_templ = Template(
        '{% load contentious %}'
        '{% editable p "my_key" editable="content,title" title=variable onclick="boogie()" %}'
        'Default content'
        '{% endeditable %}'
    )
    hideable_templ = Template(
        '{% load contentious %}'
        '{% editable div "my_key" editable="content,title,display" optional="title" title=variable %}'
        'Default content'
        '{% endeditable %}'
    )

    def _get_content_and_attrs(self, html, expected_tag_name):
        regex = '<%(tag)s\s+(?P<attrs>[^>]*)>(?P<content>.*)</%(tag)s>'
        regex = regex % {'tag': expected_tag_name}
        match = re.match(regex, html)
        self.assertIsNotNone(match)
        groupdict = match.groupdict()
        content, attrs = groupdict['content'], groupdict['attrs']
        return content, attrs


    @mock.patch("contentious.templatetags.contentious.api", new=no_op_api)
    def test_tag_rendering(self):
        """ Test that {% editable %} renders the HTML tag as we expect it to. """
        context = Context({'variable': 'variable_value'})
        result = self.templ.render(context)
        content, attrs = self._get_content_and_attrs(result, 'div')
        #We're not in edit mode, so we expect our attrs and content to be un-fiddled with
        self.assertEqual(content, 'Default content')
        self.assertTrue(re.search('(^|\s|\b)onclick="boogie\(\)"(\B|\s|$)', attrs))
        #our 'title' attribute had a variable value, which should have been taken from context
        self.assertTrue(re.search('(^|\s|\b)title="variable_value"(\B|\s|$)', attrs))
        #We do *not* expect any of the data-X attributes or the cts-editable class
        self.assertFalse("data-" in attrs)
        self.assertFalse("cts-editable" in attrs)

    @mock.patch("contentious.templatetags.contentious.api", new=edit_mode_no_op_api)
    def test_tag_rendering_in_edit_mode(self):
        """ Test that when we're in edit mode the tag is rendered the same as when
            not in edit mode, but with the addition of the data-x attributes.
        """
        context = Context({'variable': 'variable_value'})
        result = self.templ.render(context)
        content, attrs = self._get_content_and_attrs(result, 'div')
        #We expect the attributes that we specified to be rendered, the same as when not in edit mode
        self.assertEqual(content, 'Default content')
        self.assertTrue(re.search('(^|\s|\b)onclick="boogie\(\)"(\B|\s|$)', attrs))
        #our 'title' attribute had a variable value, which should have been taken from context
        self.assertTrue(re.search('(^|\s|\b)title="variable_value"(\B|\s|$)', attrs))
        #And we also expect the tag to have the relevant data-X attributes for the editing
        expected_data_attrs = {
            "data-cts-key": "my_key",
            "data-cts-editables": "content,title",
            "data-cts-optionals": "title",
            "class": "cts-editable cts-default-data", #not a data attribute, but only apears in edit mode
        }
        for attr, value in expected_data_attrs.items():
            expected_str = '%s="%s"' % (attr, value)
            self.assertTrue(expected_str in attrs, "%s not found in attrs" % expected_str)

    @mock.patch("contentious.templatetags.contentious.api", new=configurable_api)
    def test_hideable_tag_rendering(self):
        """ Test that a hideable tag is shown/hidden depending on its display property """
        configurable_api.set_return_value('in_edit_mode', False)
        data = {
            "display": False
        }
        configurable_api.set_return_value('get_content_data', data)
        result = self.hideable_templ.render(Context())
        self.assertFalse(result)

        data = {
            "display": True
        }
        configurable_api.set_return_value('get_content_data', data)
        result = self.hideable_templ.render(Context())
        self.assertTrue(result)

    @mock.patch("contentious.templatetags.contentious.api", new=edit_mode_no_op_api)
    def test_editable_as_variable(self):
        """ Test that the 'editable' kwarg can be passed as a variable in
            the context.  This isn't covered by the other tests.
        """
        templ = Template(
            '{% load contentious %}'
            '{% editable div "my_key" editable=editable_variable %}'
            '{% endeditable %}'
        )
        context = Context({'editable_variable': ['title', 'content', 'tabindex']})
        result = templ.render(context)
        content, attrs = self._get_content_and_attrs(result, 'div')
        self.assertTrue('data-cts-editables="title,content,tabindex"' in attrs)

    @mock.patch("contentious.templatetags.contentious.api", new=configurable_api)
    def test_rendering_using_data_from_api(self):
        """ Test that the tag correctly uses data returned from the API, including
            escaping of HTML characters if the data is expected to be text.
        """
        data = {
            "content": "<strong>Badger loves mashed potato!</strong>",
            "title": "<strong>HTML does not belong in the title attribute.</strong>"
        }
        configurable_api.set_return_value('get_content_data', data)
        configurable_api.set_return_value('in_edit_mode', True)
        context = Context({'variable': 'variable_value'})
        result = self.templ.render(context)
        content, attrs = self._get_content_and_attrs(result, 'div')
        #Because the HTML tag is a <div> we don't expect the content to be escaped
        self.assertEqual(content, data["content"])
        #But we still expect the title to be escaped because HTML in the title would be crazy
        expected_title = 'title="%s"' % escape(data["title"])
        self.assertTrue(expected_title in attrs)
        #Now we render the <p> tag, which should have everything escaped
        result = self.p_templ.render(context)
        content, attrs = self._get_content_and_attrs(result, 'p')
        self.assertEqual(content, escape(data["content"]))
        expected_title = 'title="%s"' % escape(data["title"])
        self.assertTrue(expected_title in attrs)
        #Test the other stuff is still fine
        expected_data_attrs = {
            "data-cts-key": "my_key",
            "data-cts-editables": "content,title",
            "class": "cts-editable", #not a data attribute, but only apears in edit mode
        }
        for attr, value in expected_data_attrs.items():
            expected_str = '%s="%s"' % (attr, value)
            self.assertTrue(expected_str in attrs, "%s not found in attrs" % expected_str)

    def test_pre_render(self):
        """ Test that if the API has a pre_render() method, that it can
            effectively modify the tag.
        """
        templ = Template(
            '{% load contentious %}'
            '{% editable div "my_key" editable="content" title="cake" %}'
            'badger'
            '{% endeditable %}'
        )
        api = ConfigurableAPI()
        api.set_return_value('get_content_data', {})
        api.set_return_value('in_edit_mode', False)
        with mock.patch('contentious.templatetags.contentious.api', new=api):
            #First test that things don't die if the API doesn't have a pre_render()
            #method, and that the output is as expected
            result = templ.render(Context({}))
            content, attrs = self._get_content_and_attrs(result, 'div')
            self.assertTrue('badger' in content)
            self.assertTrue('title="cake"' in attrs)
        #Now add a pre_render method to our API, and test that the tag_spec which
        #it returns is used to render the HTML tag
        new_tag_spec = {
            "tag_name": "span",
            "attrs": {"title": "pony", "onclick": "apocalypse('fast');"},
            "content": "I am not a teapot",
        }
        api.pre_render = lambda tag_spec, meta: new_tag_spec
        with mock.patch('contentious.templatetags.contentious.api', new=api):
            #First test that things don't die if the API doesn't have a pre_render()
            #method, and that the output is as expected
            result = templ.render(Context({}))
            content, attrs = self._get_content_and_attrs(result, 'span')
            self.assertTrue('I am not a teapot' in content)
            self.assertTrue('title="pony"' in attrs)
            self.assertTrue('''onclick="apocalypse('fast');"''' in attrs)

    def test_editable_and_optional_can_be_empty(self):
        """ Test that it's possible to define editable="" or optional="", and
            that these are correctly passed to the API's pre_render() method
            as empty lists, not [''].
        """
        templ = Template(
            '{% load contentious %}'
            '{% editable div "my_key" editable="" optional="" %}'
            '{% endeditable %}'
        )
        def _pre_render(tag_spec, meta):
            self.assertEqual(meta['editables'], [])
            self.assertEqual(meta['optionals'], [])
            return tag_spec

        api = ConfigurableAPI()
        api.set_return_value('get_content_data', {})
        api.set_return_value('in_edit_mode', False)
        api.pre_render = _pre_render
        with mock.patch('contentious.templatetags.contentious.api', new=api):
            templ.render(Context({}))



class EditDialogueTest(TestCase):
    """ Test case for the {% contentious_edit_dialogue %} tag. """

    def test_contentious_edit_dialogue(self):
        """ Test basic rendering of the {% contentious_edit_dialogue %} tag. """
        templ = Template(
            '{% load contentious %}'
            '{% contentious_edit_dialogue %}'
        )


class ToolbarTagTest(TestCase):

    templ_normal_tag = Template(
        '{% load contentious %}'
        '{% toolbar %}'
    )
    templ_tag_custom_templ = Template(
        '{% load contentious %}'
        '{% toolbar "contentious/tests/test_toolbar.html" %}'
    )

    @mock.patch("contentious.templatetags.contentious.api", new=configurable_api)
    def test_tag_gets_included_correctly(self):
        configurable_api.set_return_value('in_edit_mode', True)
        context = Context()
        result = self.templ_normal_tag.render(context)
        self.assertTrue(any([
            'cls-toolbar' in result,
            'cls-highlight-editables' in result,
            'cts-highlight-hidden-editables' in result
        ]))

    @mock.patch("contentious.templatetags.contentious.api", new=configurable_api)
    def test_custom_template(self):
        configurable_api.set_return_value('in_edit_mode', True)
        context = Context()
        result = self.templ_tag_custom_templ.render(context)
        self.assertTrue(any([
            'cls-toolbar' in result,
            'cls-highlight-editables' in result,
            'cts-highlight-hidden-editables' in result,
            'cls-test-edit-mode-exit' in result
        ]))

    @mock.patch("contentious.templatetags.contentious.api", new=configurable_api)
    def test_tag_does_not_get_included_if_in_edit_mode_is_false(self):
        configurable_api.set_return_value('in_edit_mode', False)
        context = Context()
        result = self.templ_normal_tag.render(context)
        self.assertEqual(result, "")


