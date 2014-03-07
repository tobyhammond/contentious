

class NoOpAPI(object):
    """ An implementation of the ContentiousInterface which just does nothing. """

    def in_edit_mode(self, context):
        return False

    def get_content_data(self, key, context):
        return {}

    def save_content_data(self, key, data, context):
        pass


class EditModeNoOpAPI(NoOpAPI):
    """ Same as NoOpAPI but returns True for in_edit_mode. """

    def in_edit_mode(self, context):
        return True


class ConfigurableAPI(object):
    """ Mock API which makes it easy to set what the return values are. """

    def __init__(self):
        self.return_values = {}

    def set_return_value(self, method_name, value):
        self.return_values[method_name] = value

    def _get_return_value(self, method_name):
        return self.return_values[method_name]

    def in_edit_mode(self, context):
        return self._get_return_value("in_edit_mode")

    def get_content_data(self, key, context):
        return self._get_return_value("get_content_data")

    def save_content_data(self, key, data, context):
        pass #irrelevant
