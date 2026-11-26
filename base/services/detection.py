import cv2
import numpy as np
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.segmentation import watershed


def detect_cells(
    binary_image: np.ndarray,
    min_area: float | None = None,
    min_distance: int | None = None
) -> list[np.ndarray]:
    """
    Detect potential cells in a binary image
    by splitting touching foreground regions with watershed. Default size
    thresholds scale from a 512-pixel reference image.
    """

    foreground = binary_image > 0

    if not np.any(foreground):
        return []

    scale = min(binary_image.shape[:2]) / 512
    if min_area is None:
        min_area = max(1.0, 20 * scale ** 2)
    if min_distance is None:
        min_distance = max(1, round(10 * scale))

    distance = cv2.distanceTransform(
        foreground.astype(np.uint8),
        cv2.DIST_L2,
        5
    )

    connected_components, _ = ndi.label(foreground)
    peak_coordinates = peak_local_max(
        distance,
        min_distance=min_distance,
        labels=connected_components,
        exclude_border=False
    )

    markers = np.zeros(distance.shape, dtype=np.int32)
    markers[tuple(peak_coordinates.T)] = np.arange(
        1,
        len(peak_coordinates) + 1
    )

    labels = watershed(
        -distance,
        markers,
        mask=foreground
    )

    cells = []

    for label, region in enumerate(ndi.find_objects(labels), start=1):
        if region is None:
            continue

        y_slice, x_slice = region
        region_mask = (labels[region] == label).astype(np.uint8)
        contours, _ = cv2.findContours(
            region_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
            offset=(x_slice.start, y_slice.start)
        )

        cells.extend(
            contour for contour in contours
            if cv2.contourArea(contour) >= min_area
        )

    return cells