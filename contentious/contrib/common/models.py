import urlparse

from django.db import models


#TODO: Add validators for the fields on the ContentItemBase model, e.g.
#make sure that href/src are valid URLs


class ContentItemBase(models.Model):
    """ Abstract base class for storing edited content data.
        Essentially one of these objects stores the data for a single piece
        of content, or single editable HTML tag (they're the same thing).

        It is expected that you create a subclass of this and add your own
        fields, such as `language` or whatever you're using to segregate your
        content (if anything).  You don't have to use this though, you can
        save data to any storage mechanism you want to.  Just implement the
        `save_content_data` on your implementation of the ContentiousAPI.
    """
    class Meta:
        abstract = True

    content_fields = (
        'content',
        'href',
        'src',
        'title',
        'target'
    )

    key = models.CharField(max_length=100)
    content = models.TextField(blank=True)
    display = models.NullBooleanField(default=True)

    #This list of attributs could be extended, or could be stored as JSON :-/
    href = models.CharField(max_length=500, blank=True)
    src = models.CharField(max_length=500, blank=True)
    title = models.CharField(max_length=500, blank=True)
    target = models.CharField(max_length=20, blank=True)

    @property
    def content_dict(self):
        """ Return a dict of the values that store content data. """
        return {field: getattr(self, field) for field in self.content_fields}

    def clean(self):
        if self.src:
            parsed = urlparse.urlparse(self.src)
            if parsed.scheme:
                self.src = urlparse.urlunparse(('',) + parsed[1:])
