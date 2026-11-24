import tempfile
import cv2
import numpy as np

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from base.models import CellImage
from base.services.image_processing import process_cell_image


class ImageProcessingTests(TestCase):

    def setUp(self):

        # Use temporary media storage
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.media_settings = override_settings(
            MEDIA_ROOT=self.temp_dir.name
        )

        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)

        # Create a test user
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpassword123"
        )

        # Generate a synthetic microscopy image
        image = np.zeros((256, 256), dtype=np.uint8)

        cv2.circle(image, (50, 50), 15, 255, -1)
        cv2.circle(image, (120, 120), 15, 255, -1)
        cv2.circle(image, (200, 200), 15, 255, -1)

        success, encoded = cv2.imencode(".png", image)

        self.assertTrue(success)

        uploaded_file = SimpleUploadedFile(
            name="test_cells.png",
            content=encoded.tobytes(),
            content_type="image/png"
        )

        self.cell_image = CellImage.objects.create(
            user=self.user,
            uploaded_image=uploaded_file
        )

    def test_uploaded_image_exists(self):

        field = self.cell_image.uploaded_image

        self.assertTrue(
            field.storage.exists(field.name)
        )

    def test_create_automatically_processes_image(self):

        self.cell_image.refresh_from_db()

        self.assertEqual(self.cell_image.cell_count, 3)
        self.assertGreater(self.cell_image.average_area_px2, 0)
        self.assertEqual(len(self.cell_image.measurements), 3)
        self.assertTrue(bool(self.cell_image.processed_image))
        self.assertGreaterEqual(self.cell_image.processing_time_ms, 0)

    def test_process_cell_image(self):

        process_cell_image(self.cell_image)

        self.cell_image.refresh_from_db()

        self.assertEqual(
            self.cell_image.cell_count, 3
        )

        self.assertGreater(
            self.cell_image.average_area_px2, 0
        )

        self.assertEqual(
            len(self.cell_image.measurements), 3
        )

        self.assertGreaterEqual(
            self.cell_image.processing_time_ms, 0
        )

    def test_processed_image_saved(self):

        process_cell_image(self.cell_image)

        self.cell_image.refresh_from_db()

        field = self.cell_image.processed_image

        self.assertTrue(bool(field))

        self.assertTrue(
            field.storage.exists(field.name)
        )

        self.assertTrue(
            field.name.startswith("cell_images/processed/")
        )

    def test_image_ownership_preserved(self):

        process_cell_image(self.cell_image)

        self.cell_image.refresh_from_db()

        self.assertEqual(
            self.cell_image.user, self.user
        )

    def test_invalid_image(self):

        invalid_file = SimpleUploadedFile(
            name="invalid.png",
            content=b"not an actual image",
            content_type="image/png"
        )

        with self.assertRaises(ValueError):
            CellImage.objects.create(
                user=self.user,
                uploaded_image=invalid_file
            )

        invalid_image = CellImage.objects.latest("pk")
        invalid_image.refresh_from_db()

        self.assertFalse(bool(invalid_image.processed_image))
        self.assertIsNone(invalid_image.cell_count)