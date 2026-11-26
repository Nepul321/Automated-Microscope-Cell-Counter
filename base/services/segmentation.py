import cv2
import numpy as np


def threshold_image(image: np.ndarray) -> np.ndarray:
    """
    Correct uneven background illumination and threshold the cell foreground.
    """

    sigma = max(3.0, min(image.shape[:2]) / 8.0)
    background = cv2.GaussianBlur(
        image,
        (0, 0),
        sigmaX=sigma,
        sigmaY=sigma
    )
    corrected = np.clip(
        image.astype(np.int16) - background.astype(np.int16) + 128,
        0,
        255
    ).astype(np.uint8)

    _, binary_image = cv2.threshold(
        corrected,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    if np.count_nonzero(binary_image) > binary_image.size / 2:
        binary_image = cv2.bitwise_not(binary_image)

    return binary_image