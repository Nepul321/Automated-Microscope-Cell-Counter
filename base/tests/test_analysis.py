import cv2
import numpy as np

from django.test import SimpleTestCase
from base.services.analysis import analyze_image
from base.services.detection import detect_cells


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

    def test_dark_cells_on_bright_background(self):
        image = 255 - self.image

        results = analyze_image(image)

        self.assertEqual(results["cell_count"], 3)

    def test_cells_under_uneven_illumination(self):
        image = np.tile(
            np.linspace(35, 180, 512, dtype=np.float32),
            (512, 1)
        )
        cell_mask = np.zeros((512, 512), dtype=np.uint8)
        centers = [
            (60, 70), (160, 70), (260, 70), (360, 70), (460, 70),
            (60, 220), (160, 220), (260, 220), (360, 220), (460, 220),
            (60, 390), (160, 390), (260, 390), (360, 390), (460, 390)
        ]
        for center in centers:
            cv2.circle(cell_mask, center, 12, 1, -1)

        bright_cells = image.copy()
        bright_cells[cell_mask > 0] += 45
        dark_cells = image.copy()
        dark_cells[cell_mask > 0] -= 45

        for image_variant in (bright_cells, dark_cells):
            results = analyze_image(
                np.clip(image_variant, 0, 255).astype(np.uint8)
            )
            self.assertEqual(results["cell_count"], len(centers))

    def test_touching_cells_are_separated(self):
        image = np.zeros((128, 128), dtype=np.uint8)
        cv2.circle(image, (45, 64), 15, 255, -1)
        cv2.circle(image, (70, 64), 15, 255, -1)

        results = analyze_image(image)

        self.assertEqual(results["cell_count"], 2)

    def test_nearby_separate_cells_are_both_detected(self):
        image = np.zeros((64, 64), dtype=np.uint8)
        cv2.circle(image, (20, 32), 3, 255, -1)
        cv2.circle(image, (29, 32), 3, 255, -1)

        self.assertEqual(len(detect_cells(image)), 2)

    def test_small_cells_scale_with_image_dimensions(self):
        image = np.zeros((256, 256), dtype=np.uint8)
        for center in ((50, 64), (100, 64), (150, 64)):
            cv2.circle(image, center, 2, 255, -1)

        self.assertEqual(len(detect_cells(image)), 3)

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