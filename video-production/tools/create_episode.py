#!/usr/bin/env python3
"""Create a new episode folder from the workspace templates.

Usage:
    python tools/create_episode.py --id 001 --title "Example Topic"
    python tools/create_episode.py --id 002 --title "Example Series" --mode series

A documentary is the default: a 16:9 video with one narration and one final video. A series is a
vertical 9:16 story that is cut into numbered parts. Both use the same folders and the same engine.

Uses only the Python standard library. Refuses to touch an existing episode:
an episode ID can be used once, whatever its title.
"""

import argparse
import json
import re
import shutil
import sys
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
EPISODES = ROOT / "episodes"
MAX_SLUG_LENGTH = 60

SUBFOLDERS = (
    "01_research",
    "02_script",
    "03_narration/audio",
    "03_narration/transcript",
    "03_narration/subtitles",
    "04_storyboard",
    "05_google_flow_images/prompts",
    "05_google_flow_images/generated",
    "05_google_flow_images/approved",
    "06_google_flow_animations/prompts",
    "06_google_flow_animations/generated",
    "06_google_flow_animations/approved",
    "07_remotion/source",
    "07_remotion/renders",
    "07_remotion/previews",
    "08_sound_design/cues",
    "08_sound_design/effects",
    "08_sound_design/music",
    "09_editing/projects",
    "09_editing/previews",
    "09_editing/qa",
    "10_final_export/video",
    "10_final_export/thumbnail",
    "10_final_export/metadata",
)


def episode_id(value):
    """Normalize an ID to at least three digits, so 1 and 001 are the same episode."""
    value = value.strip()
    if not (value.isascii() and value.isdigit()):
        raise argparse.ArgumentTypeError(f"'{value}' is not valid: use digits only, such as 001")
    return value.zfill(3)


def episode_title(value):
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("the title cannot be empty")
    return value


def safe_slug(title):
    """Turn any title into a folder-safe name, keeping letters from every language."""
    text = unicodedata.normalize("NFKC", title).casefold()
    text = re.sub(r"['’]", "", text)
    text = "".join(c if unicodedata.category(c)[0] in "LMN" else "-" for c in text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:MAX_SLUG_LENGTH].rstrip("-") or "untitled"


def find_existing(number):
    if not EPISODES.is_dir():
        return []
    return [p for p in EPISODES.iterdir() if p.name == number or p.name.startswith(number + "_")]


def write_json_template(template_name, destination, update):
    data = json.loads((TEMPLATES / template_name).read_text(encoding="utf-8"))
    update(data)
    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


SERIES_PLATFORMS = ["facebook_reels", "youtube_shorts"]


def series_assembly(data):
    """Settings for a vertical series. Everything else stays as in the documentary template."""
    data["production_mode"] = "series"
    data["master_aspect_ratio"] = "9:16"
    data["target_platforms"] = list(SERIES_PLATFORMS)
    data["width"] = 1080
    data["height"] = 1920
    data["series_part_target_seconds"] = 60


def populate(folder, number, title, folder_name, mode="documentary"):
    for subfolder in SUBFOLDERS:
        (folder / subfolder).mkdir(parents=True)

    storyboard = (TEMPLATES / "storyboard-template.md").read_text(encoding="utf-8")
    storyboard = storyboard.replace("{{EPISODE_ID}}", number).replace("{{EPISODE_TITLE}}", title)
    (folder / "04_storyboard" / "storyboard.md").write_text(storyboard, encoding="utf-8")

    shutil.copyfile(
        TEMPLATES / "scene-timeline-template.csv",
        folder / "04_storyboard" / "scene_timeline.csv",
    )

    def fill_manifest(data):
        data["episode"].update(id=number, title=title)

    def fill_status(data):
        data["episode"].update(
            id=number,
            title=title,
            folder=folder_name,
            created_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        )

    write_json_template(
        "asset-manifest-template.json", folder / "04_storyboard" / "asset_manifest.json", fill_manifest
    )
    write_json_template(
        "production-status-template.json", folder / "production_status.json", fill_status
    )

    assembly = json.loads((TEMPLATES / "assembly-template.json").read_text(encoding="utf-8"))
    if mode == "series":
        series_assembly(assembly)
    (folder / "09_editing" / "projects" / "assembly.json").write_text(
        json.dumps(assembly, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    if mode == "series":
        manifest = json.loads((TEMPLATES / "series-manifest-template.json").read_text(encoding="utf-8"))
        manifest["series"]["id"] = safe_slug(title)
        manifest["series"]["title"] = title
        (folder / "04_storyboard" / "series_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    shutil.copyfile(
        TEMPLATES / "sound-cues-template.json",
        folder / "08_sound_design" / "cues" / "sound_cues.json",
    )


def main():
    # A title in any language must not crash printing on a non-UTF-8 console.
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

    parser = argparse.ArgumentParser(description="Create a new video episode folder.")
    parser.add_argument("--id", required=True, type=episode_id, help="episode number, such as 001")
    parser.add_argument("--title", required=True, type=episode_title, help="episode title")
    parser.add_argument(
        "--mode",
        choices=("documentary", "series"),
        default="documentary",
        help="documentary (default, 16:9, one video) or series (9:16, numbered parts)",
    )
    args = parser.parse_args()

    existing = find_existing(args.id)
    if existing:
        print(f"ERROR: episode {args.id} already exists: {existing[0]}", file=sys.stderr)
        print("Nothing was changed. Choose a different --id.", file=sys.stderr)
        return 1

    folder_name = f"{args.id}_{safe_slug(args.title)}"
    target = EPISODES / folder_name
    EPISODES.mkdir(exist_ok=True)

    # Build in a staging folder and rename at the end, so a failure never leaves
    # a half-made episode. The rename also fails if the target already exists.
    staging = Path(tempfile.mkdtemp(prefix=".creating-", dir=EPISODES))
    try:
        populate(staging, args.id, args.title, folder_name, args.mode)
        staging.rename(target)
    except (OSError, ValueError, KeyError) as error:
        print(f"ERROR: could not create the episode: {error}", file=sys.stderr)
        return 1
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    print(f"Created episode {args.id}: {target}")
    print()
    print("Add your completed files, then tell Claude Code DONE:")
    print(f"  Final script  -> {target / '02_script'}")
    print(f"  Audio         -> {target / '03_narration' / 'audio'}")
    print(f"  Transcript    -> {target / '03_narration' / 'transcript'}")
    print(f"  Subtitles     -> {target / '03_narration' / 'subtitles'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
