#SYSTEM
import json

#LIBRARIES
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.test import TestCase
import mock

#CONTENTIOUS
from contentious.views import save_content as save_content_view
from contentious.tests.mocks import (
    EditModeNoOpAPI,
)


class ViewsTest(TestCase):
    """ Tests for the contentious view function(s). """

    def test_save_content(self):
        """ Test the save_content() view. """
        data = {'key': 'my_key', 'content': 'my content', 'onlick': 'rabbits()'}
        mock_api = EditModeNoOpAPI()
        request = HttpRequest()
        request.method = 'POST'
        request.POST = data
        #Test that in a 'normal' situation our view calls the api's save_content_data
        #method and returns a 200 response
        with mock.patch.object(mock_api, "save_content_data") as mock_api_save_data:
            with mock.patch("contentious.views.api", new=mock_api):
                with mock.patch("contentious.decorators.api", new=mock_api):
                    response = save_content_view(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(mock_api_save_data.call_count, 1)
            expected_data_for_save = data.copy()
            expected_key_for_save = expected_data_for_save.pop('key') #cunning
            self.assertEqual( mock_api_save_data.call_args[0][0], expected_key_for_save)
            self.assertEqual( mock_api_save_data.call_args[0][1], expected_data_for_save)
        #Test that if the api raises a ValidationError that the view function returns a
        #JSON response containing the errors dict
        error_dict = {'onlick': 'Sorry, rabbits() is not valid.'}
        def raise_error(*args, **kwargs):
            """ Mock for the save_content_data method of the api. """
            raise ValidationError(error_dict)
        with mock.patch.object(mock_api, "save_content_data", new=raise_error):
            with mock.patch("contentious.views.api", new=mock_api):
                with mock.patch("contentious.decorators.api", new=mock_api):
                    response = save_content_view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), error_dict)
