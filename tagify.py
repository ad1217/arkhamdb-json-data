#!/usr/bin/env python3

import json
from pathlib import Path
import re
import sys

try:
    BASE_DIR = Path(__file__).parent
except NameError:
    BASE_DIR = Path(".")

PACK_DIR = BASE_DIR / "pack"
OUTPUT_DIR = PACK_DIR / "zzz_retagged_cards"


def find_text_options():
    for json_file in PACK_DIR.glob("**/*.json"):
        with open(json_file) as f:
            data = json.load(f)
        for card in data:
            if "deck_options" in card and card["deck_options"] is not None:
                for option in card["deck_options"]:
                    if "text" in option:
                        try:
                            option["re"] = [re.compile(t) for t in option["text"]]
                        except re.error as e:
                            print(
                                f"Regex for {card['name']} [{card['code']}] "
                                f"in {json_file.relative_to(BASE_DIR)} failed to compile: {e}"
                            )
                            sys.exit(1)
                        yield option


def tags_for_card(options, card):
    for option in options:
        if any(r.search(card["text"]) for r in option["re"]):
            yield from option.get("tag", [])


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
        print(
            f"Changed tags on {len(tagged_cards)} cards in {json_file.relative_to(BASE_DIR)}"
        )
        with open(OUTPUT_DIR / json_file.name, "w") as f:
            json.dump(tagged_cards, f, indent=4)
