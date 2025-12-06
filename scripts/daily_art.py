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

    total_pages = data["pagination"]["total_pages"]
    random_page = random.randint(1, total_pages)

    params_page = dict(params_base)
    params_page["page"] = random_page

    resp = requests.get(AIC_SEARCH_URL, params=params_page, timeout=20)
    resp.raise_for_status()
    artworks = resp.json().get("data", [])

    for art in artworks:
        if art.get("image_id"):
            return art

    raise RuntimeError("No artworks with valid image_id found on random page.")


def make_image_url(image_id: str) -> str:
    return f"{IIIF_BASE}/{image_id}/full/843,/0/default.jpg"


def make_web_url(art_id: int) -> str:
    return f"https://www.artic.edu/artworks/{art_id}"


def build_markdown_block(art: dict) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")

    title = art.get("title") or "Untitled"
    artist = art.get("artist_display") or "Unknown artist"
    date_display = art.get("date_display") or "Unknown date"
    art_id = art["id"]
    image_url = make_image_url(art["image_id"])
    web_url = make_web_url(art_id)

    return textwrap.dedent(
        f"""
        **Date (UTC): {today}**

        [![{title}]({image_url})]({web_url})

        **{title}**  
        {artist}  
        {date_display}  

        Source: [Art Institute of Chicago]({web_url})
        """
    ).strip()


def update_readme(new_block: str):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if MARKER_START not in content or MARKER_END not in content:
        raise RuntimeError("Daily Art markers missing in README.md")

    before, _, rest = content.partition(MARKER_START)
    _, _, after = rest.partition(MARKER_END)

    updated = (
        before
        + MARKER_START
        + "\n\n"
        + new_block
        + "\n\n"
        + MARKER_END
        + after
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)


def main():
    try:
        art = get_random_public_domain_artwork()
        block = build_markdown_block(art)
        update_readme(block)
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()
