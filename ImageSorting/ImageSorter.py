"""
Requirements:
    python -m pip install opencv-python numpy --break-system-packages

Usage:
    # Uses ./Images (next to the script) and writes ./Target.zip by default
    python ImageSorter.py

    # Or override either path explicitly
    python ImageSorter.py --input ./SomeOtherFolder --output Target.zip --top 10
"""

import argparse
import glob
import math
import os
import zipfile

import cv2
import numpy as np

# tried at multiple strictness levels since a single fixed threshold doesn't
# work across different lighting/material conditions (e.g. bright red on a
# dark background vs. a red line over warm-toned leather/wood)
THRESHOLD_LEVELS = [
    (120, 100),   # loose
    (155, 135),   # medium
    (190, 175),   # strict
]


def score_ring_at_threshold(red_mask):
    close_kernel = np.ones((5, 5), np.uint8)
    cleaned = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, close_kernel, iterations=2)
    open_kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, open_kernel, iterations=1)

    contours, hierarchy = cv2.findContours(cleaned, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return 0.0, None
    hierarchy = hierarchy[0]

    best_score = 0.0
    best_circle = None

    for i, h_row in enumerate(hierarchy):
        _, _, first_child, _ = h_row
        if first_child == -1:
            continue  # no hole -> not a ring candidate

        outer = contours[i]
        inner = contours[first_child]
        if cv2.contourArea(outer) < 50 or cv2.contourArea(inner) < 5:
            continue

        (ox, oy), r_outer = cv2.minEnclosingCircle(outer)
        (ix, iy), r_inner = cv2.minEnclosingCircle(inner)
        if r_outer < 8 or r_inner < 2:
            continue

        center_dist = math.hypot(ox - ix, oy - iy)
        concentricity = 1.0 - min(1.0, center_dist / max(r_outer, 1))

        thickness = r_outer - r_inner
        if thickness <= 0:
            continue
        thickness_ratio = thickness / r_outer

        ideal_outer_area = math.pi * r_outer ** 2
        outer_circularity = 1.0 - min(1.0, abs(cv2.contourArea(outer) - ideal_outer_area) / ideal_outer_area)
        ideal_inner_area = math.pi * r_inner ** 2
        inner_circularity = 1.0 - min(1.0, abs(cv2.contourArea(inner) - ideal_inner_area) / ideal_inner_area)

        # penalize thick/filled rings -- a real outline is thin relative to its size
        thinness_score = 1.0 if thickness_ratio < 0.35 else max(0.0, 1.0 - (thickness_ratio - 0.35) * 3)

        score = concentricity * outer_circularity * inner_circularity * thinness_score

        if score > best_score:
            best_score = score
            best_circle = (ox, oy, r_outer)

    return best_score, best_circle


def detect_red_circle_score(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return 0.0, None

    target_max_dim = 800
    h, w = img.shape[:2]
    scale = target_max_dim / max(h, w)
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    best_score = 0.0
    best_circle = None

    for (s_min, v_min) in THRESHOLD_LEVELS:
        lower_red1 = np.array([0, s_min, v_min])
        upper_red1 = np.array([7, 255, 255])
        lower_red2 = np.array([173, s_min, v_min])
        upper_red2 = np.array([180, 255, 255])
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        score, circle = score_ring_at_threshold(red_mask)
        if score > best_score:
            best_score = score
            best_circle = circle

    return best_score, best_circle


def find_top_red_circle_images(input_dir, top_n=10):
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff")
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(input_dir, ext)))
        image_paths.extend(glob.glob(os.path.join(input_dir, ext.upper())))

    # dedupe -- on case-insensitive filesystems (Windows, default macOS),
    # "*.jpg" and "*.JPG" match the SAME files, so every image was being
    # added twice, doubling the scan and filling the zip with duplicates
    seen = set()
    deduped_paths = []
    for path in image_paths:
        key = os.path.normcase(os.path.abspath(path))
        if key not in seen:
            seen.add(key)
            deduped_paths.append(path)
    image_paths = deduped_paths

    if not image_paths:
        print(f"No images found in {input_dir}")
        return []

    results = []
    for path in sorted(image_paths):
        score, circle = detect_red_circle_score(path)
        results.append((path, score, circle))
        if score > 0.05:
            print(f"  MATCH  {os.path.basename(path):40s} score={score:.3f} circle={circle}")
        else:
            print(f"  ------ {os.path.basename(path):40s} score={score:.3f}")

    results.sort(key=lambda r: r[1], reverse=True)
    return results[:top_n]


def zip_images(matches, output_zip):
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, score, circle in matches:
            zf.write(path, arcname=os.path.basename(path))
    print(f"\nWrote {len(matches)} image(s) to {output_zip}")


def main():
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
        print("\nNo images found. Nothing to zip.")
        return

    zip_images(matches, args.output)


if __name__ == "__main__":
    main()