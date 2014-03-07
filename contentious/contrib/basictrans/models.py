from django.db import models

from contentious.contrib.common.models import ContentItemBase


class TranslationContent(ContentItemBase):
    """ Model for storing simple translations. """

    class Meta:
        app_label = "contentious"
        unique_together = (
            ('language', 'key'),
        )

    language = models.CharField(max_length=7)
