#!/usr/bin/env python3
"""Generate BG2 reference notes with Gemini, one markdown file per topic.

Usage: GEMINI_API_KEY=... scripts/bg2_knowledge.py [--grounded] [--force] [filter ...]
Output: knowledge/bg2/<slug>.md (existing files are skipped unless --force).
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
OUT = Path(__file__).resolve().parent.parent / "knowledge" / "bg2"
DELAY_SECONDS = 8

PROMPT = """Write a markdown reference note about: {topic}

Game: Baldur's Gate II: Shadows of Amn (original game rules, base game only).
Throne of Bhaal content is NOT installed: do not include it, and do not spoil past the end of Shadows of Amn.

Rules:
- Begin with a single H1 heading that contains the full topic name and "BG2".
- Use short sections with H2 headings and bullet lists. Plain markdown only, no tables.
- Give exact names, locations, and numbers. Name the area or map for every location.
- If you are not sure of a fact, write "unknown" instead of guessing.
- Note where Enhanced Edition differs from the original game, if it matters.
- Keep it under 700 words."""

COMPANIONS = ["Imoen", "Jaheira", "Minsc and Boo", "Jan Jansen", "Viconia", "Aerie", "Anomen",
              "Cernd", "Edwin", "Haer'Dalis", "Keldorn", "Korgan", "Mazzy", "Nalia", "Valygar", "Yoshimo"]

TOPICS = (
    [f"Companion: {c}. Class, stats, kit, personal quest, how to recruit, key dialogue choices, and best equipment" for c in COMPANIONS]
    + [f"Shadows of Amn Chapter {n}: walkthrough, main quest steps, key areas, and side quests available" for n in range(1, 8)]
    + [
        "Cleric class in BG2: spell progression, turning undead, weapon proficiencies, and armor",
        "Berserker kit: abilities, berserk rage, restrictions, and how it plays",
        "Dual-classing a human into Berserker and Cleric: level requirements, when abilities return, and pitfalls",
        "Flails and morningstars: every notable weapon in Shadows of Amn, where to get each, and its stats",
        "Best armor and shields obtainable in Shadows of Amn chapters 4 to 7, with locations",
        "Cleric spells levels 1 to 5: what each does and which are worth memorizing",
        "Cleric spells levels 6 to 7 and their value in Shadows of Amn",
        "Combat mechanics: THAC0, Armor Class, saving throws, attacks per round, and speed factor",
        "Proficiency and weapon specialization rules in BG2",
        "Experience and level caps in Shadows of Amn, and how to level efficiently",
        "Stores and merchants in Athkatla: what each sells and buys, and notable items",
        "The Underdark and Ust Natha in chapter 4 to 5: walkthrough and dangers",
        "Spellhold and the Asylum: walkthrough and dangers",
        "Irenicus's Dungeon: walkthrough, and the Planar Sphere and Shadow Thieves quests",
        "Athkatla city districts: Docks, Bridge, Slums, Temple, Government, and Promenade",
        "Dragons and other optional bosses in Shadows of Amn: levels, locations, and strategies",
        "Party composition advice with Jaheira, Minsc, and Jan for a cleric and berserker protagonist",
        "Romances available in Shadows of Amn and how each one progresses",
        "Stronghold options for a cleric: Temple of Helm or Torm, Stronghold quests, and rewards",
        "Common undead, demon, and golem enemies: weaknesses and which weapons or spells to use",
    ]
)

PLAYTHROUGH = """# My BG2 playthrough (notes for the assistant)

- Game: Baldur's Gate II: Shadows of Amn. Throne of Bhaal is not installed yet.
- Current progress: Chapter 4.
- Protagonist: human dual-classed Berserker and Cleric, level 9 in each class.
- Weapon build: flail and morningstar.
- Party: Jaheira, Minsc, Jan, plus two others (fill in).
- Goal: advice should fit this party, level, and chapter, and avoid spoilers past Shadows of Amn.
"""


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:70]


def generate(topic, key, grounded):
    body = {"contents": [{"parts": [{"text": PROMPT.format(topic=topic)}]}]}
    if grounded:
        body["tools"] = [{"google_search": {}}]
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.load(resp)
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 4:
                time.sleep(30 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} from Gemini: {e.read().decode()[:300]}") from None
    raise RuntimeError("retries exhausted")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filter", nargs="*", help="only topics containing any of these words")
    ap.add_argument("--force", action="store_true", help="regenerate existing files")
    ap.add_argument("--grounded", action="store_true", help="use Google Search grounding")
    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY is not set")

    OUT.mkdir(parents=True, exist_ok=True)
    playthrough = OUT / "00-my-playthrough.md"
    if not playthrough.exists():
        playthrough.write_text(PLAYTHROUGH)

    topics = [t for t in TOPICS if not args.filter or any(f.lower() in t.lower() for f in args.filter)]
    for i, topic in enumerate(topics, 1):
        path = OUT / f"{slugify(topic)}.md"
        if path.exists() and not args.force:
            print(f"[{i}/{len(topics)}] skip {path.name}")
            continue
        print(f"[{i}/{len(topics)}] {topic[:60]}")
        try:
            path.write_text(generate(topic, key, args.grounded) + "\n")
        except (RuntimeError, KeyError, IndexError) as e:
            print(f"  failed: {e}", file=sys.stderr)
        time.sleep(DELAY_SECONDS)


if __name__ == "__main__":
    main()
