#!/usr/bin/env python3

import os
import random
import textwrap
from datetime import datetime

import requests

AIC_SEARCH_URL = "https://api.artic.edu/api/v1/artworks/search"
IIIF_BASE = "https://www.artic.edu/iiif/2"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(REPO_ROOT, "README.md")

MARKER_START = "<!-- AIC_DAILY_ART_START -->"
MARKER_END = "<!-- AIC_DAILY_ART_END -->"


def get_random_public_domain_artwork():
    params_base = {
        "query[term][is_public_domain]": "true",
        "fields": "id,title,artist_display,date_display,image_id",
        "limit": 1,
    }

    resp = requests.get(AIC_SEARCH_URL, params=params_base, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    pagination = data.get("pagination", {})
    total_pages = pagination.get("total_pages", 1)
    if total_pages < 1:
        raise RuntimeError("No public-domain artworks found from AIC API.")

    random_page = random.randint(1, total_pages)
    params_page = dict(params_base)
    params_page["page"] = random_page

    resp = requests.get(AIC_SEARCH_URL, params=params_page, timeout=20)
    resp.raise_for_status()
    page_data = resp.json()
    artworks = page_data.get("data", [])

    if not artworks:
        raise RuntimeError("Random page returned no artworks.")

    for art in artworks:
        if art.get("image_id"):
            return art

    raise RuntimeError("No artworks with image_id on this random page.")


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

    image_url = make_image_url(image_id)
    web_url = make_web_url(art_id)

    block = textwrap.dedent(
        f"""
        **Date (UTC): {today_str}**

        [![{title}]({image_url})]({web_url})

        **{title}**  
        {artist_display}  
        {date_display}  

        Source: [Art Institute of Chicago]({web_url})
        """
    ).strip()

    return block


def update_readme_section(new_block: str) -> None:
    if not os.path.exists(README_PATH):
        raise FileNotFoundError(f"README not found at {README_PATH}")

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if MARKER_START not in content or MARKER_END not in content:
        raise RuntimeError(
            "Markers not found in README. "
            "Ensure both AIC markers are present."
        )

    before, _start, rest = content.partition(MARKER_START)
    _middle, _end, after = rest.partition(MARKER_END)

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
    else:
        print("README unchanged; nothing to write.")


def main():
    try:
        art = get_random_public_domain_artwork()
    except Exception as exc:
        print(f"Error fetching artwork from AIC API: {exc}")
        return

    block = build_markdown_block(art)

    try:
        update_readme_section(block)
    except Exception as exc:
        print(f"Error updating README: {exc}")


if __name__ == "__main__":
    main()
