#!/usr/bin/env python3

import json
from pathlib import Path
import re

try:
    PACK_DIR = Path(__file__).parent / "pack"
except NameError:
    PACK_DIR = Path("pack")

OUTPUT_DIR = PACK_DIR / "zzz_retagged_cards"


def find_text_options():
    for json_file in PACK_DIR.glob("**/*.json"):
        with open(json_file) as f:
            data = json.load(f)
        for card in data:
            if "deck_options" in card and card["deck_options"] is not None:
                for option in card["deck_options"]:
                    if "text" in option:
                        option["re"] = [re.compile(t) for t in option["text"]]
                        yield option


def tags_for_card(options, card):
    for option in options:
        if any(r.search(card["text"]) for r in option["re"]):
            yield from option["tag"]


if OUTPUT_DIR.is_dir():
    for file in OUTPUT_DIR.glob("*.json"):
        file.unlink()
else:
    OUTPUT_DIR.mkdir()

options = list(find_text_options())
for json_file in PACK_DIR.glob("**/*.json"):
    with open(json_file) as f:
        data = json.load(f)
    tagged_cards = []
    for card in data:
        if (
            "type_code" in card
            and card["type_code"] in {"event", "skill", "asset"}
            and "text" in card
        ):
            new_tags = set(tags_for_card(options, card))
            old_tags = set(card.get("tags", "").split(".")) - {""}
            if new_tags - old_tags:
                card["tags"] = ".".join(sorted(old_tags | new_tags)) + "."
                tagged_cards.append(card)

    if tagged_cards:
        print(f"Changed tags on {len(tagged_cards)} cards in {json_file.relative_to(PACK_DIR)}")
        with open(OUTPUT_DIR / json_file.name, "w") as f:
            json.dump(tagged_cards, f, indent=4)
