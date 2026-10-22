"""
Requirements:
    python -m pip install opencv-python numpy --break-system-packages

"""

import glob
import math
import os
import tempfile
import zipfile

import cv2
import numpy as np


THRESHOLD_LEVELS = [
    (120, 100),   
    (155, 135),   
    (190, 175),   
]

# This basic repeating-key XOR layer is intended for the project handoff only.
# Keep the same key and header in rebel_sever.py.
ENCRYPTION_KEY = b"ImageSorter-Rebel-Project-Key"
ENCRYPTED_HEADER = b"IMGZIPENC1\n"

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
            continue  

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

    if best_circle is not None:
        cx, cy, r = best_circle
        eff_scale = min(scale, 1.0)
        best_circle = (cx / eff_scale, cy / eff_scale, r / eff_scale)

    return best_score, best_circle


def find_top_red_circle_images(input_dir, top_n=10):
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff")
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(input_dir, ext)))
        image_paths.extend(glob.glob(os.path.join(input_dir, ext.upper())))

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


def crop_to_circle(img, circle):
    cx, cy, r = circle
    pad = int(r * 0.05) + 2  
    h, w = img.shape[:2]
    side = min(int(2 * (r + pad)), h, w)
    x1 = min(max(0, int(cx - side / 2)), w - side)
    y1 = min(max(0, int(cy - side / 2)), h - side)
    return img[y1:y1 + side, x1:x1 + side]


def encode_image(img, ext, quality):
    if ext in (".jpg", ".jpeg"):
        params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    elif ext == ".png":
        params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
    else:
        params = []
    ok, buf = cv2.imencode(ext, img, params)
    return buf.tobytes() if ok else None

def encrypt_file(source_path, output_path):
    """Write a marked, XOR-encrypted copy using bounded memory."""
    key_position = 0
    with open(source_path, "rb") as source, open(output_path, "wb") as output:
        output.write(ENCRYPTED_HEADER)
        while True:
            chunk = source.read(64 * 1024)
            if not chunk:
                break
            encrypted = bytes(
                byte ^ ENCRYPTION_KEY[(key_position + index) % len(ENCRYPTION_KEY)]
                for index, byte in enumerate(chunk)
            )
            output.write(encrypted)
            key_position = (key_position + len(chunk)) % len(ENCRYPTION_KEY)

def zip_images(matches, output_zip, crop=True, quality=100):
    original_bytes = 0
    output_dir = os.path.dirname(os.path.abspath(output_zip))
    fd, temporary_zip = tempfile.mkstemp(prefix="imagesorter-", suffix=".zip", dir=output_dir)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, score, circle in matches:
                name = os.path.basename(path)
                original_bytes += os.path.getsize(path)
                data = None

                if crop and circle is not None:
                    img = cv2.imread(path)
                    if img is not None:
                        cropped = crop_to_circle(img, circle)
                        if cropped.size > 0:
                            data = encode_image(cropped, os.path.splitext(name)[1].lower(), quality)
                            print(f"  cropped {name:40s} {img.shape[1]}x{img.shape[0]} -> {cropped.shape[1]}x{cropped.shape[0]}")

                if data is not None:
                    zf.writestr(name, data)
                else:
                    zf.write(path, arcname=name)
                    print(f"  kept original {name}")

        encrypt_file(temporary_zip, output_zip)
    finally:
        if os.path.exists(temporary_zip):
            os.remove(temporary_zip)

    zip_bytes = os.path.getsize(output_zip)
    print(f"\nWrote {len(matches)} image(s) to encrypted bundle {output_zip}")
    print(f"Size: {original_bytes / 1024:.0f} KB original -> {zip_bytes / 1024:.0f} KB encrypted bundle")
