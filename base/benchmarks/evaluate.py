from pathlib import Path
from time import perf_counter
import csv
import cv2
import numpy as np

from base.services.analysis import analyze_image

BASE_DIR = Path(__file__).resolve().parents[2]

IMAGE_DIR = BASE_DIR / "media" / "cell_images" / "original"
OUTPUT_DIR = Path(__file__).resolve().parent / "results"

EXPECTED_COUNT = 300

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_dataset():
    SUPPORTED_EXTENSIONS = {
        ".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp"
    }

    images = sorted(
        path for path in IMAGE_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    print(f"Found {len(images)} images")

    results = []

    for path in images:
        image = cv2.imread(
            str(path),
            cv2.IMREAD_GRAYSCALE
        )

        if image is None:
            print(f"Failed to load {path.name}")
            continue

        start = perf_counter()

        analysis = analyze_image(image)

        elapsed = (perf_counter() - start) * 1000

        detected = analysis["cell_count"]

        absolute_error = abs(
            EXPECTED_COUNT - detected
        )

        percentage_error = (
            absolute_error / EXPECTED_COUNT
        ) * 100

        results.append({
            "image": path.name,
            "expected_count": EXPECTED_COUNT,
            "detected_count": detected,
            "absolute_error": absolute_error,
            "percentage_error": round(
                percentage_error, 2
            ),
            "processing_time_ms": round(elapsed, 2)
        })

        print(
            f"{path.name}: "
            f"{detected}/{EXPECTED_COUNT} | "
            f"Error: {percentage_error:.2f}%"
        )

    return results

def summarize_results(results):
    counts = [
        result["detected_count"]
        for result in results
    ]

    errors = [
        result["absolute_error"]
        for result in results
    ]

    percentage_errors = [
        result["percentage_error"]
        for result in results
    ]

    processing_times = [
        result["processing_time_ms"]
        for result in results
    ]

    print("\n--- Evaluation Summary ---")

    print(f"Images evaluated: {len(results)}")
    print(f"Average count: {np.mean(counts):.2f}")
    print(f"Minimum count: {min(counts)}")
    print(f"Maximum count: {max(counts)}")
    print(f"MAE: {np.mean(errors):.2f}")
    print(f"MAPE: {np.mean(percentage_errors):.2f}%")
    print(f"Standard deviation: {np.std(counts):.2f}")

    print(
        f"Average processing time: "
        f"{np.mean(processing_times):.2f} ms"
    )

def export_results(results):
    output_path = OUTPUT_DIR / "baseline_v1.csv"

    with open(output_path, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys()
        )

        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    results = evaluate_dataset()

    if results:
        summarize_results(results)
        export_results(results)
    else:
        print("No images were successfully evaluated.")