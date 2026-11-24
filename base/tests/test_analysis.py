import cv2
import numpy as np

from django.test import SimpleTestCase
from base.services.analysis import analyze_image


class AnalysisTests(SimpleTestCase):

    def setUp(self):
        self.image = np.zeros(
            (256, 256),
            dtype=np.uint8
        )

        # Generate three artificial cells
        cv2.circle(self.image, (50, 50), 15, 255, -1)
        cv2.circle(self.image, (120, 120), 15, 255, -1)
        cv2.circle(self.image, (200, 200), 15, 255, -1)

    def test_cell_count(self):
        results = analyze_image(self.image)

        self.assertEqual(results["cell_count"], 3)

    def test_cell_measurements(self):
        results = analyze_image(self.image)

        self.assertEqual(len(results["measurements"]), 3)

        for cell in results["measurements"]:
            self.assertGreater(cell["area_px2"], 0)
            self.assertGreater(cell["perimeter_px"], 0)
            self.assertIsNotNone(cell["centroid_x"])
            self.assertIsNotNone(cell["centroid_y"])

    def test_average_area(self):
        results = analyze_image(self.image)

        self.assertGreater(results["average_area_px2"], 0)

    def test_annotated_image(self):
        results = analyze_image(self.image)

        annotated = results["annotated_image"]

        self.assertIsInstance(annotated, np.ndarray)
        self.assertEqual(annotated.shape, (256, 256, 3))

    def test_empty_image(self):
        image = np.zeros((256, 256), dtype=np.uint8)

        results = analyze_image(image)

        self.assertEqual(results["cell_count"], 0)
        self.assertEqual(results["measurements"], [])
        self.assertEqual(results["average_area_px2"], 0)