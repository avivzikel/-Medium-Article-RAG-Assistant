#!/usr/bin/env python3

import argparse
import csv
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print CSV article titles and text lengths.")
    parser.add_argument("--csv-path", required=True, help="Path to the CSV file.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of rows to print.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        with open(args.csv_path, newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            if not reader.fieldnames or "title" not in reader.fieldnames or "text" not in reader.fieldnames:
                print("CSV must contain 'title' and 'text' columns.", file=sys.stderr)
                raise SystemExit(1)

            for index, row in enumerate(reader):
                if index >= args.limit:
                    break

                title = row.get("title", "")
                text = row.get("text", "")
                print(f"Title: {title}")
                print(f"Text length: {len(text)}")
    except OSError as exc:
        print(f"Failed to open CSV file: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
