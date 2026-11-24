import cv2
import numpy as np


def threshold_image(image: np.ndarray) -> np.ndarray:
    """
    Separate foreground cells from the background
    using Otsu's thresholding.
    """

    threshold_value, binary_image = cv2.threshold(
        image,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return binary_image