#!/usr/bin/env python3
"""
RAW Preview Generator for OpenClaw
Scans RAW files, generates small JPG previews for WhatsApp sharing
"""

import os
import sys
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime
import re
import time

try:
    import rawpy
    import imageio
except ImportError:
    print("Installing required packages: rawpy imageio...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rawpy", "imageio"])
    import rawpy
    import imageio

try:
    from PIL import Image, ExifTags
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ExifTags

# Configuration
DB_PATH = r"x:\openclaw\workspace\raw_photos.db"  # Separate database for RAW files
PREVIEW_DIR = r"x:\openclaw\workspace\previews"
PREVIEW_SIZE = 1080  # Long edge in pixels
PREVIEW_QUALITY = 85  # JPG quality (1-100)

# Supported RAW formats
RAW_EXTENSIONS = {'.arw', '.cr2', '.nef', '.dng', '.raf', '.orf', '.rw2', '.pef', '.srw', '.cr3'}


def db_execute_with_retry(cursor, query, params=(), max_retries=5, delay=0.5):
    """Execute database query with retry logic for locked database"""
    for attempt in range(max_retries):
        try:
            cursor.execute(query, params)
            return True
        except sqlite3.OperationalError as e:
            if 'locked' in str(e) and attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))  # Exponential backoff
                continue
            else:
                raise
    return False


def parse_client_info(filepath):
    """Extract client name and date from filepath"""
    # Pattern 1: YYYY-MM-DD ClientName (with client name)
    pattern1 = r'(\d{4}-\d{2}-\d{2})\s+([^\\\/]+)'
    match = re.search(pattern1, filepath)
    if match:
        date_str = match.group(1)
        client_name = match.group(2).strip()
        return client_name, date_str

    # Pattern 2: YYYY-MM-DD (date only, no client name)
    pattern2 = r'(\d{4}-\d{2}-\d{2})[\\/]'
    match = re.search(pattern2, filepath)
    if match:
        date_str = match.group(1)
        return None, date_str

    return None, None


def get_preview_path(raw_path, preview_dir=None):
    """Generate preview JPG path from RAW path (same directory with _preview.jpg suffix)"""
    raw_file = Path(raw_path)
    # Store preview in same directory as RAW file
    preview_file = raw_file.parent / (raw_file.stem + '_preview.jpg')
    return str(preview_file)


def convert_raw_to_preview(raw_path, preview_path, max_size=1080, quality=85):
    """Convert RAW file to small JPG preview"""
    try:
        # Read RAW file
        with rawpy.imread(raw_path) as raw:
            # Extract embedded preview or process RAW
            # Using postprocess for better quality
            rgb = raw.postprocess(
                use_camera_wb=True,
                half_size=True,  # Faster processing
                no_auto_bright=False,
                output_bps=8
            )

        # Convert to PIL Image
        img = Image.fromarray(rgb)

        # Resize to target size (preserve aspect ratio)
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Create preview directory if needed
        os.makedirs(os.path.dirname(preview_path), exist_ok=True)

        # Save as JPG with optimization
        img.save(preview_path, 'JPEG', quality=quality, optimize=True, progressive=True)

        return True, os.path.getsize(preview_path)

    except Exception as e:
        return False, str(e)


def extract_exif_from_raw(raw_path):
    """Extract EXIF metadata from RAW file"""
    metadata = {
        'camera_make': None,
        'camera_model': None,
        'lens_model': None,
        'iso': None,
        'aperture': None,
        'shutter_speed': None,
        'focal_length': None,
        'datetime': None,
        'gps_latitude': None,
        'gps_longitude': None,
    }

    try:
        with rawpy.imread(raw_path) as raw:
            # Get metadata from RAW
            if hasattr(raw, 'metadata'):
                # Camera info
                metadata['camera_make'] = getattr(raw.metadata, 'make', None)
                metadata['camera_model'] = getattr(raw.metadata, 'model', None)

                # Exposure settings
                metadata['iso'] = getattr(raw.metadata, 'iso_speed', None)

                # Aperture
                if hasattr(raw.metadata, 'aperture'):
                    metadata['aperture'] = f"f/{raw.metadata.aperture:.1f}"

                # Shutter speed
                if hasattr(raw.metadata, 'shutter'):
                    ss = raw.metadata.shutter
                    if ss >= 1:
                        metadata['shutter_speed'] = f"{ss:.1f}s"
                    else:
                        metadata['shutter_speed'] = f"1/{int(1/ss)}"

                # Focal length
                if hasattr(raw.metadata, 'focal_length'):
                    metadata['focal_length'] = f"{raw.metadata.focal_length:.0f}mm"

                # Timestamp
                if hasattr(raw.metadata, 'timestamp'):
                    metadata['datetime'] = datetime.fromtimestamp(raw.metadata.timestamp)

    except Exception as e:
        print(f"Warning: Could not extract EXIF from {raw_path}: {e}")

    return metadata


def scan_raw_files(directory, update_db=True, regenerate=False, limit=None):
    """Scan directory for RAW files and generate previews"""
    print(f"\nScanning: {directory}")
    print("Looking for RAW files...")

    raw_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if Path(file).suffix.lower() in RAW_EXTENSIONS:
                raw_files.append(os.path.join(root, file))
                if limit and len(raw_files) >= limit:
                    break
        if limit and len(raw_files) >= limit:
            break

    print(f"Found {len(raw_files)} RAW files")

    if not raw_files:
        print("No RAW files found!")
        return

    # Connect to database
    conn = None
    if update_db:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        # Enable WAL mode for better concurrent access
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()

        # Create raw_photos table if it doesn't exist
        db_execute_with_retry(cursor, '''
            CREATE TABLE IF NOT EXISTS raw_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE NOT NULL,
                preview_path TEXT,
                client_name TEXT,
                date TEXT,
                camera_make TEXT,
                camera_model TEXT,
                lens_model TEXT,
                iso INTEGER,
                aperture TEXT,
                shutter_speed TEXT,
                focal_length TEXT,
                datetime TEXT,
                gps_latitude REAL,
                gps_longitude REAL,
                size_mb REAL,
                preview_size_kb REAL,
                indexed_at TEXT
            )
        ''')
        conn.commit()

    # Process each RAW file
    processed = 0
    skipped = 0
    failed = 0

    for idx, raw_path in enumerate(raw_files, 1):
        print(f"\r  Processing {idx}/{len(raw_files)}...", end='', flush=True)

        # Generate preview path
        preview_path = get_preview_path(raw_path, PREVIEW_DIR)

        # Skip if preview exists and regenerate=False
        if not regenerate and os.path.exists(preview_path):
            skipped += 1
            continue

        # Convert RAW to preview
        success, result = convert_raw_to_preview(raw_path, preview_path, PREVIEW_SIZE, PREVIEW_QUALITY)

        if not success:
            print(f"\n  Failed: {raw_path}: {result}")
            failed += 1
            continue

        preview_size_kb = result / 1024
        processed += 1

        # Extract metadata if updating database
        if update_db:
            client_name, date = parse_client_info(raw_path)
            metadata = extract_exif_from_raw(raw_path)
            raw_size_mb = os.path.getsize(raw_path) / (1024 * 1024)

            # Insert/update database
            try:
                db_execute_with_retry(cursor, '''
                    INSERT OR REPLACE INTO raw_photos (
                        filepath, preview_path, client_name, date,
                        camera_make, camera_model, lens_model,
                        iso, aperture, shutter_speed, focal_length,
                        datetime, gps_latitude, gps_longitude,
                        size_mb, preview_size_kb, indexed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    raw_path, preview_path, client_name, date,
                    metadata['camera_make'], metadata['camera_model'], metadata['lens_model'],
                    metadata['iso'], metadata['aperture'], metadata['shutter_speed'], metadata['focal_length'],
                    metadata['datetime'], metadata['gps_latitude'], metadata['gps_longitude'],
                    raw_size_mb, preview_size_kb, datetime.now().isoformat()
                ))
            except Exception as e:
                print(f"\n  Database error for {raw_path}: {e}")

        # Commit every 50 files
        if update_db and processed % 50 == 0:
            conn.commit()

    print(f"\r  Processed {len(raw_files)} RAW files")

    if update_db:
        conn.commit()
        conn.close()

    print(f"\nResults:")
    print(f"  Generated: {processed} previews")
    print(f"  Skipped: {skipped} (already exist)")
    print(f"  Failed: {failed}")
    print(f"\nPreviews stored in: {PREVIEW_DIR}")


def search_raw_photos(client=None, date=None, limit=50):
    """Search RAW photos database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT filepath, preview_path, client_name, date, camera_model FROM raw_photos WHERE 1=1"
    params = []

    if client:
        query += " AND client_name LIKE ?"
        params.append(f"%{client}%")

    if date:
        query += " AND date = ?"
        params.append(date)

    query += f" ORDER BY date DESC LIMIT {limit}"

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    return results


def main():
    parser = argparse.ArgumentParser(description='RAW Preview Generator for OpenClaw')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan directory for RAW files')
    scan_parser.add_argument('directory', help='Directory to scan')
    scan_parser.add_argument('--no-db', action='store_true', help='Skip database update')
    scan_parser.add_argument('--regenerate', action='store_true', help='Regenerate existing previews')
    scan_parser.add_argument('--limit', type=int, help='Limit number of files to process (for testing)')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search RAW photos')
    search_parser.add_argument('--client', help='Client name')
    search_parser.add_argument('--date', help='Date (YYYY-MM-DD)')
    search_parser.add_argument('--limit', type=int, default=50, help='Max results')

    args = parser.parse_args()

    if args.command == 'scan':
        scan_raw_files(args.directory, update_db=not args.no_db, regenerate=args.regenerate, limit=args.limit)

    elif args.command == 'search':
        results = search_raw_photos(args.client, args.date, args.limit)
        for filepath, preview_path, client, date, camera in results:
            print(f"{date} | {client} | {camera}")
            print(f"  RAW: {filepath}")
            print(f"  Preview: {preview_path}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
