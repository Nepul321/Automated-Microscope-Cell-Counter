from django.contrib import admin
from .models import CellImage


@admin.register(CellImage)
class CellImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "cell_count",
        "average_area_px2",
        "processing_time_ms",
    )
    readonly_fields = (
        "processed_image",
        "cell_count",
        "average_area_px2",
        "measurements",
        "processing_time_ms",
    )