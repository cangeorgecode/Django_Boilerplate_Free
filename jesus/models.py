from django.db import models

class Verse(models.Model):
    verse = models.CharField(max_length=255)

    def __str__(self):
        return self.verse
