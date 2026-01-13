#!/usr/bin/env python3

import os
import random
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
        "limit": 1,
    }

    r = requests.get(AIC_SEARCH_URL, params=base_params, timeout=20)
    r.raise_for_status()
    meta = r.json().get("pagination", {})

    total_pages = meta.get("total_pages", 1)
    if total_pages < 1:
        raise RuntimeError("No public domain artworks returned by API")

    page = random.randint(1, total_pages)
    params = dict(base_params)
    params["page"] = page

    r = requests.get(AIC_SEARCH_URL, params=params, timeout=20)
    r.raise_for_status()

    data = r.json().get("data", [])

    for art in data:
        if art.get("image_id"):
            return art

    raise RuntimeError("No artwork with image_id found on random page")


def make_image_url(image_id: str) -> str:
    return f"{IIIF_BASE}/{image_id}/full/843,/0/default.jpg"


def make_web_url(art_id: int) -> str:
    return f"https://www.artic.edu/artworks/{art_id}"


def build_markdown_block(art: dict) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")

    art_id = art.get("id")
    title = art.get("title") or "Untitled"
    artist = art.get("artist_display") or "Unknown artist"
    date = art.get("date_display") or "Date unknown"
    image_id = art.get("image_id")

    image_url = make_image_url(image_id)
    web_url = make_web_url(art_id)

    return (
        f"**Date (UTC): {today}**\n\n"
        f"[![{title}]({image_url})]({web_url})\n\n"
        f"**{title}**  \n"
        f"{artist}  \n"
        f"{date}  \n\n"
        f"Source: [Art Institute of Chicago]({web_url})"
    )


def update_readme_section(new_block: str) -> None:
    if not os.path.exists(README_PATH):
        raise FileNotFoundError(f"README not found at {README_PATH}")

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if MARKER_START not in content or MARKER_END not in content:
        raise RuntimeError("AIC markers not found in README")

    before, _, rest = content.partition(MARKER_START)
    _, _, after = rest.partition(MARKER_END)

    replacement = (
        MARKER_START
        + "\n\n"
        + new_block
        + "\n\n"
        + MARKER_END
    )

    new_content = before + replacement + after

    if new_content != content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)


def main() -> None:
    try:
        art = get_random_public_domain_artwork()
    except Exception as e:
        print(f"Failed to fetch artwork: {e}")
        return

    block = build_markdown_block(art)

    try:
        update_readme_section(block)
    except Exception as e:
        print(f"Failed to update README: {e}")


if __name__ == "__main__":
    main()

