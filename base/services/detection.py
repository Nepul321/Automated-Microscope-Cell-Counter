import cv2
import numpy as np


def detect_cells(
    binary_image: np.ndarray,
    min_area: float = 20
) -> list[np.ndarray]:
    """
    Detect potential cells in a binary image
    using contour detection.
    """

    contours, _ = cv2.findContours(
        binary_image.astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    cells = [
        contour for contour in contours
        if cv2.contourArea(contour) >= min_area
    ]

    return cells