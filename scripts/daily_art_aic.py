#!/usr/bin/env python3

import os
import random
import sys
from datetime import datetime

import requests

AIC_SEARCH_URL = "https://api.artic.edu/api/v1/artworks/search"
IIIF_BASE = "https://www.artic.edu/iiif/2"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(REPO_ROOT, "README.md")

MARKER_START = "<!-- AIC_DAILY_ART_START -->"
MARKER_END = "<!-- AIC_DAILY_ART_END -->"


def get_random_public_domain_artwork() -> dict:
    
    base_params = {
        "query[term][is_public_domain]": "true",
        "fields": "id,title,artist_display,date_display,image_id",
        "limit": 100,
    }

    r = requests.get(AIC_SEARCH_URL, params=base_params, timeout=20)
    r.raise_for_status()
    j = r.json()

    pagination = j.get("pagination", {})
    total_pages = int(pagination.get("total_pages", 1) or 1)
    if total_pages < 1:
        raise RuntimeError("No public-domain artworks found from AIC API.")

    page = random.randint(1, total_pages)
    params = dict(base_params)
    params["page"] = page

    r = requests.get(AIC_SEARCH_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json().get("data", []) or []

    candidates = [a for a in data if a.get("image_id")]
    if not candidates:
        raise RuntimeError("Random page returned no artworks with image_id.")

    return random.choice(candidates)


def make_image_url(image_id: str) -> str:
    return f"{IIIF_BASE}/{image_id}/full/843,/0/default.jpg"


def make_web_url(art_id: int) -> str:
    return f"https://www.artic.edu/artworks/{art_id}"


def build_markdown_block(art: dict) -> str:
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    art_id = art.get("id")
    title = art.get("title") or "Untitled"
    artist_display = art.get("artist_display") or "Unknown artist"
    date_display = art.get("date_display") or "Date unknown"
    image_id = art.get("image_id")
    if not image_id:
        raise RuntimeError("Artwork missing image_id after filtering (unexpected).")

    image_url = make_image_url(image_id)
    web_url = make_web_url(art_id)


    return (
        f"**Date (UTC): {today_str}**\n\n"
        f"[![{title}]({image_url})]({web_url})\n\n"
        f"**{title}**  \n"
        f"{artist_display}  \n"
        f"{date_display}  \n\n"
        f"Source: [Art Institute of Chicago]({web_url})"
    )


def update_readme_section(new_block: str) -> None:
    if not os.path.exists(README_PATH):
        raise FileNotFoundError(f"README not found at {README_PATH}")

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if MARKER_START not in content or MARKER_END not in content:
        raise RuntimeError("Markers not found in README. Ensure both AIC markers are present.")

    before, _, rest = content.partition(MARKER_START)
    _, _, after = rest.partition(MARKER_END)

    replacement = f"{MARKER_START}\n\n{new_block}\n\n{MARKER_END}"
    new_content = before + replacement + after

    if new_content == content:
        print("README unchanged; nothing to write.")
        return

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


def main() -> None:
    art = get_random_public_domain_artwork()
    block = build_markdown_block(art)
    update_readme_section(block)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Daily art update failed: {exc}", file=sys.stderr)
        sys.exit(1)

