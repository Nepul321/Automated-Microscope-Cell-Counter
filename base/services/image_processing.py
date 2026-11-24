import cv2
import numpy as np

from time import perf_counter
from django.core.files.base import ContentFile

from .analysis import analyze_image
from base.models import CellImage


def process_cell_image(cell_image: CellImage) -> CellImage:

    # 1. Read the uploaded image
    with cell_image.uploaded_image.open("rb") as file:
        image_bytes = file.read()

    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:
        raise ValueError("Unable to decode uploaded image.")

    # 2. Execute the analysis pipeline
    start = perf_counter()

    results = analyze_image(image)

    elapsed = (perf_counter() - start) * 1000

    # 3. Encode the annotated image
    success, encoded = cv2.imencode(
        ".png",
        results["annotated_image"]
    )

    if not success:
        raise ValueError("Unable to encode processed image.")

    # 4. Save the processed image
    filename = f"cell_image_{cell_image.pk}_processed.png"

    cell_image.processed_image.save(
        filename,
        ContentFile(encoded.tobytes()),
        save=False
    )

    # 5. Store analysis results
    cell_image.cell_count = results["cell_count"]
    cell_image.average_area_px2 = results["average_area_px2"]
    cell_image.measurements = results["measurements"]
    cell_image.processing_time_ms = round(elapsed, 2)

    # 6. Update the database
    cell_image.save(update_fields=[
        "processed_image",
        "cell_count",
        "average_area_px2",
        "measurements",
        "processing_time_ms"
    ])

    return cell_image