import numpy as np

from .preprocessing import preprocess_image
from .segmentation import threshold_image
from .detection import detect_cells
from .measurement import measure_cells
from .annotation import annotate_image


def analyze_image(image: np.ndarray) -> dict:

    preprocessed = preprocess_image(image)

    binary = threshold_image(preprocessed)

    cells = detect_cells(binary)

    measurements = measure_cells(cells)

    annotated = annotate_image(image, cells)

    average_area = (
        sum(cell["area_px2"] for cell in measurements)
        / len(measurements)
        if measurements else 0
    )

    return {
        "cell_count": len(cells),
        "average_area_px2": round(average_area, 2),
        "measurements": measurements,
        "annotated_image": annotated
    }