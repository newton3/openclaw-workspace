#!/usr/bin/env python3
"""
Unified Photo Search - Searches both JPG and RAW photo databases
"""

import sqlite3
import argparse
import os

JPG_DB = r"x:\openclaw\workspace\photos_full.db"
RAW_DB = r"x:\openclaw\workspace\raw_photos.db"


def search_all_photos(client=None, date=None, camera=None, location=False, limit=50):
    """Search both JPG and RAW databases"""
    results = []

    # Search JPG database
    if os.path.exists(JPG_DB):
        try:
            conn = sqlite3.connect(JPG_DB, timeout=5.0)
            cursor = conn.cursor()

            query = "SELECT filepath, client_name, date, camera_model, 'JPG' as type FROM photos WHERE 1=1"
            params = []

            if client:
                query += " AND client_name LIKE ?"
                params.append(f"%{client}%")
            if date:
                query += " AND date = ?"
                params.append(date)
            if camera:
                query += " AND camera_model LIKE ?"
                params.append(f"%{camera}%")
            if location:
                query += " AND gps_latitude IS NOT NULL AND gps_longitude IS NOT NULL"

            query += f" ORDER BY date DESC LIMIT {limit}"

            cursor.execute(query, params)
            results.extend(cursor.fetchall())
            conn.close()
        except Exception as e:
            print(f"Warning: Could not search JPG database: {e}")

    # Search RAW database (with previews)
    if os.path.exists(RAW_DB):
        try:
            conn = sqlite3.connect(RAW_DB, timeout=5.0)
            cursor = conn.cursor()

            query = "SELECT preview_path, client_name, date, camera_model, 'RAW' as type FROM raw_photos WHERE preview_path IS NOT NULL AND 1=1"
            params = []

            if client:
                query += " AND client_name LIKE ?"
                params.append(f"%{client}%")
            if date:
                query += " AND date = ?"
                params.append(date)
            if camera:
                query += " AND camera_model LIKE ?"
                params.append(f"%{camera}%")
            if location:
                query += " AND gps_latitude IS NOT NULL AND gps_longitude IS NOT NULL"

            query += f" ORDER BY date DESC LIMIT {limit}"

            cursor.execute(query, params)
            results.extend(cursor.fetchall())
            conn.close()
        except Exception as e:
            print(f"Warning: Could not search RAW database: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(description='Search all photos (JPG + RAW)')
    parser.add_argument('query', nargs='?', help='Quick search by client name')
    parser.add_argument('--client', help='Client name')
    parser.add_argument('--date', help='Date (YYYY-MM-DD)')
    parser.add_argument('--camera', help='Camera model')
    parser.add_argument('--location', action='store_true', help='Only photos with GPS')
    parser.add_argument('--limit', type=int, default=50, help='Max results (default: 50)')
    parser.add_argument('--count', action='store_true', help='Just count results')
    parser.add_argument('--simple', action='store_true', help='Simple output (paths only)')

    args = parser.parse_args()

    # Handle quick search (positional argument)
    if args.query:
        args.client = args.query

    # Search
    results = search_all_photos(
        client=args.client,
        date=args.date,
        camera=args.camera,
        location=args.location,
        limit=args.limit
    )

    if args.count:
        print(f"Total photos found: {len(results)}")
        jpg_count = sum(1 for r in results if r[4] == 'JPG')
        raw_count = sum(1 for r in results if r[4] == 'RAW')
        print(f"  JPG: {jpg_count}")
        print(f"  RAW previews: {raw_count}")
        return

    if args.simple:
        for filepath, _, _, _, _ in results:
            print(filepath)
        return

    # Detailed output
    print(f"\nFound {len(results)} photos:\n")
    for filepath, client, date, camera, photo_type in results:
        print(f"[{photo_type}] {date or 'unknown'} | {client or 'unknown'} | {camera or 'unknown'}")
        print(f"  {filepath}")
        print()


if __name__ == '__main__':
    main()
