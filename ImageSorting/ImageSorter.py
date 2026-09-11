"""
Requirements:
    pip install opencv-python numpy --break-system-packages

Usage:
    # Uses ./Images (next to the script) and writes ./Target.zip by default
    python ImageSorter.py

    # Or override either path explicitly
    python ImageSorter.py --input ./SomeOtherFolder --output Target.zip --top 10
"""

import argparse
import glob
import os
import zipfile

import cv2
import numpy as np


def detect_red_circle_score(image_path):
    """
    Returns a confidence score (float) for how strongly this image
    contains a red circle OUTLINE. 0.0 means no red circle was detected.
    """
    img = cv2.imread(image_path)
    if img is None:
        return 0.0, None

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 100, 80])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 80])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    kernel = np.ones((5, 5), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)

    blurred_mask = cv2.GaussianBlur(red_mask, (9, 9), 2)

    circles = cv2.HoughCircles(
        blurred_mask,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=40,
        param1=50,
        param2=25,
        minRadius=10,
        maxRadius=0,
    )

    if circles is None:
        return 0.0, None

    circles = np.round(circles[0, :]).astype("int")

    best_score = 0.0
    best_circle = None

    for (x, y, r) in circles:
        ring_thickness = max(3, r // 6)
        ring_mask = np.zeros(red_mask.shape, dtype="uint8")
        cv2.circle(ring_mask, (x, y), r, 255, thickness=ring_thickness)

        ring_area = np.count_nonzero(ring_mask)
        if ring_area == 0:
            continue

        overlap = cv2.bitwise_and(red_mask, ring_mask)
        red_fraction = np.count_nonzero(overlap) / ring_area

        score = r * red_fraction

        if score > best_score:
            best_score = score
            best_circle = (x, y, r)

    return best_score, best_circle


def find_top_red_circle_images(input_dir, top_n=10):
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff")
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(input_dir, ext)))
        image_paths.extend(glob.glob(os.path.join(input_dir, ext.upper())))

    if not image_paths:
        print(f"No images found in {input_dir}")
        return []

    results = []
    for path in sorted(image_paths):
        score, circle = detect_red_circle_score(path)
        if score > 0.0:
            results.append((path, score, circle))
            print(f"  MATCH  {os.path.basename(path):40s} score={score:8.2f} circle={circle}")
        else:
            print(f"  ------ {os.path.basename(path):40s} no red circle detected")

    # Highest score first
    results.sort(key=lambda r: r[1], reverse=True)
    return results[:top_n]


def zip_images(matches, output_zip):
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, score, circle in matches:
            zf.write(path, arcname=os.path.basename(path))
    print(f"\nWrote {len(matches)} image(s) to {output_zip}")


def main():
    # Default paths are relative to THIS SCRIPT's location, not the
    # current working directory -- so it works the same regardless of
    # where you run it from, as long as "Images" sits next to the script.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(script_dir, "Images")
    default_output = os.path.join(script_dir, "Target.zip")

    parser = argparse.ArgumentParser(description="Find images with red circle outlines and zip the top matches.")
    parser.add_argument(
        "--input",
        default=default_input,
        help=f"Folder containing the images to scan (default: {default_input})",
    )
    parser.add_argument(
        "--output",
        default=default_output,
        help=f"Path for the output zip file (default: {default_output})",
    )
    parser.add_argument("--top", type=int, default=10, help="Number of top matching images to zip (default: 10)")
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"ERROR: input folder not found: {args.input}")
        print("Make sure a folder named 'Images' exists in the same directory as this script,")
        print("or pass a different folder with --input.")
        return

    print(f"Scanning '{args.input}' for red circle outlines...\n")
    matches = find_top_red_circle_images(args.input, top_n=args.top)

    if not matches:
        print("\nNo images with red circle outlines were found. Nothing to zip.")
        return

    zip_images(matches, args.output)


if __name__ == "__main__":
    main()