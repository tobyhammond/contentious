#SYSTEM

#LIBRARIES
from django.test import TestCase
from django.utils.safestring import mark_safe

#CONTENTIOUS
from contentious.utils import recursive_make_safe


class UtilsTest(TestCase):
    """ Tests for functions in utils.py. """

    def test_recursive_make_safe(self):
        """ Test the recursive_make_safe() function. """
        tests = (
            #input, expected_output
            (
                '<script>bad();</script>',
                '&lt;script&gt;bad();&lt;/script&gt;'
            ),
            (
                mark_safe('<script>bad();</script>'),
                '<script>bad();</script>'
            ),
            (
                ['<script>bad();</script>', 'hello'],
                ['&lt;script&gt;bad();&lt;/script&gt;', 'hello']
            ),
            (
                {'a': 'sausage', 'b': '<blink>HELLO</blink>'},
                {'a': 'sausage', 'b': '&lt;blink&gt;HELLO&lt;/blink&gt;'}
            ),
            (
                {'a': ['<p>hello</p>', 'something', {'b': '<blink>HELLO</blink>'}]},
                {'a': ['&lt;p&gt;hello&lt;/p&gt;', 'something', {'b': '&lt;blink&gt;HELLO&lt;/blink&gt;'}]},
            ),
        )
        for inp, expected in tests:
            self.assertEqual(recursive_make_safe(inp), expected)
