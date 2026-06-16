#!/usr/bin/env python3

import argparse
import csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print CSV article titles and text lengths.")
    parser.add_argument("--csv-path", required=True, help="Path to the CSV file.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of rows to print.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with open(args.csv_path, newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for index, row in enumerate(reader):
            if index >= args.limit:
                break

            title = row.get("title", "")
            text = row.get("text", "")
            print(f"Title: {title}")
            print(f"Text length: {len(text)}")


if __name__ == "__main__":
    main()
