from django.db import models
from django.contrib.auth.models import User

class CellImage(models.Model):
    uploaded_image = models.ImageField(upload_to="cell_images/uploaded/")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    processed_image = models.ImageField(blank=True, upload_to="cell_images/processed/", null=True)

    cell_count = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    average_area_px2 = models.FloatField(
        null=True,
        blank=True
    )

    measurements = models.JSONField(
        default=list,
        blank=True
    )

    processing_time_ms = models.FloatField(
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        uploaded_changed = is_new

        if not is_new:
            previous_name = (
                type(self).objects
                .filter(pk=self.pk)
                .values_list("uploaded_image", flat=True)
                .first()
            )
            uploaded_changed = previous_name != str(self.uploaded_image)

        if uploaded_changed and kwargs.get("update_fields"):
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"uploaded_image"}

        super().save(*args, **kwargs)

        if not uploaded_changed or not self.uploaded_image:
            return

        if getattr(self, "_processing_image", False):
            return

        self._processing_image = True
        try:
            from base.services.image_processing import process_cell_image
            process_cell_image(self)
        finally:
            del self._processing_image

    def __str__(self):
        return f"CellImage {self.pk}"
