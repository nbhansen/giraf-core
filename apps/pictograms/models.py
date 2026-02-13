"""Pictogram model.

Pictograms are visual aids used for communication with autistic children.
They can belong to an organization (custom) or be global (organization=None).
"""
from django.db import models


class Pictogram(models.Model):
    """A visual aid image used across GIRAF apps."""

    name = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="pictograms",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pictograms"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
