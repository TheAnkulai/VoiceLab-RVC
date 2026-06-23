from __future__ import annotations

import argparse
import shutil
import sys
import urllib.request
from pathlib import Path


RVC_DOWNLOAD_LINK = "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/"

# In VoiceLab-RVC this file is expected to be placed in the project root:
# VoiceLab-RVC/download_models.py
BASE_DIR = Path(__file__).resolve().parent

MODELS = [
    {
        "name": "hubert_base.pt",
        "url": RVC_DOWNLOAD_LINK + "hubert_base.pt",
        "path": BASE_DIR / "assets" / "hubert" / "hubert_base.pt",
        "description": "HuBERT content encoder, required for RVC inference",
    },
    {
        "name": "rmvpe.pt",
        "url": RVC_DOWNLOAD_LINK + "rmvpe.pt",
        "path": BASE_DIR / "assets" / "rmvpe" / "rmvpe.pt",
        "description": "RMVPE F0 extractor, required only for f0-method rmvpe",
    },
]


def format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "unknown size"

    size = float(size_bytes)
    units = ["B", "KB", "MB", "GB"]

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size_bytes} B"


def download_file(url: str, destination: Path, force: bool = False) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not force:
        print(f"SKIP: {destination} already exists")
        return

    temp_path = destination.with_suffix(destination.suffix + ".part")

    print(f"Downloading:")
    print(f"  from: {url}")
    print(f"  to:   {destination}")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "VoiceLab-RVC downloader"},
    )

    try:
        with urllib.request.urlopen(request) as response:
            total_size_header = response.headers.get("Content-Length")
            total_size = int(total_size_header) if total_size_header else None

            downloaded = 0
            chunk_size = 1024 * 1024

            with temp_path.open("wb") as file:
                while True:
                    chunk = response.read(chunk_size)

                    if not chunk:
                        break

                    file.write(chunk)
                    downloaded += len(chunk)

                    if total_size:
                        percent = downloaded / total_size * 100
                        print(
                            f"\r  {percent:6.2f}% "
                            f"({format_size(downloaded)} / {format_size(total_size)})",
                            end="",
                            flush=True,
                        )
                    else:
                        print(
                            f"\r  downloaded {format_size(downloaded)}",
                            end="",
                            flush=True,
                        )

        print()
        shutil.move(str(temp_path), str(destination))
        print(f"OK: {destination}")

    except Exception:
        if temp_path.exists():
            temp_path.unlink()

        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download required base models for VoiceLab-RVC."
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Redownload files even if they already exist.",
    )

    parser.add_argument(
        "--no-rmvpe",
        action="store_true",
        help="Download only HuBERT and skip RMVPE.",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("VoiceLab-RVC model downloader")
    print("=" * 70)
    print(f"Project folder: {BASE_DIR}")
    print()

    selected_models = MODELS

    if args.no_rmvpe:
        selected_models = [
            item for item in MODELS
            if item["name"] != "rmvpe.pt"
        ]

    for item in selected_models:
        print("-" * 70)
        print(f"{item['name']} — {item['description']}")
        download_file(
            url=item["url"],
            destination=item["path"],
            force=args.force,
        )

    print()
    print("=" * 70)
    print("Done.")
    print("=" * 70)

    missing = [
        item["path"] for item in selected_models
        if not item["path"].exists()
    ]

    if missing:
        print("Missing files:")
        for path in missing:
            print(f"  {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
