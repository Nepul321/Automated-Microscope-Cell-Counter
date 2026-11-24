import cv2
import numpy as np


def annotate_image(
    image: np.ndarray,
    cells: list[np.ndarray]
) -> np.ndarray:

    if image.ndim == 2:
        annotated = cv2.cvtColor(
            image, cv2.COLOR_GRAY2BGR
        )
    else:
        annotated = image.copy()

    cv2.drawContours(
        annotated,
        cells,
        -1,
        (0, 255, 0),
        1
    )

    return annotated