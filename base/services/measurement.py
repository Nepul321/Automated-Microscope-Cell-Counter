import cv2
import numpy as np
import math


def measure_cells(cells: list[np.ndarray]) -> list[dict]:
    measurements = []

    for index, contour in enumerate(cells, start=1):
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        moments = cv2.moments(contour)

        if moments["m00"] != 0:
            cx = moments["m10"] / moments["m00"]
            cy = moments["m01"] / moments["m00"]
        else:
            cx, cy = None, None

        circularity = (
            (4 * math.pi * area) / perimeter**2
            if perimeter > 0 else 0
        )

        diameter = math.sqrt(4 * area / math.pi)

        measurements.append({
            "cell_id": index,
            "area_px2": round(area, 2),
            "perimeter_px": round(perimeter, 2),
            "centroid_x": round(cx, 2) if cx is not None else None,
            "centroid_y": round(cy, 2) if cy is not None else None,
            "circularity": round(circularity, 4),
            "equivalent_diameter_px": round(diameter, 2)
        })

    return measurements