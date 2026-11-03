#!/usr/bin/env python3
"""Validate Google Flow JSON exports (schema v1.0) for one episode folder.

Usage: python validate_flow_json.py <episode_folder>
Exit code 0 = all checks passed, 1 = errors found, 2 = nothing to validate.
Standard: shared/prompts/FLOW_JSON_GENERATION_STANDARD.md
"""
import csv
import json
import re
import sys
from pathlib import Path

ALLOWED_VIDEO_DURATIONS = {4, 6, 8}  # single source of truth; confirm against Flow Queue Studio X
MAX_JOBS = 10
SCENE_RE = re.compile(r"^S\d{3,}$")
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
DUR_RE = re.compile(r"^Image-to-video\. Use the approved still (S\d+) as the first frame and visual reference\. Duration: (\d+(?:\.\d+)?) seconds?\.")
REQUIRED = ("job_id", "scene_id", "type", "prompt", "source_image", "output_name")
KINDS = {
    "IMAGES": ("05_google_flow_images/prompts", {"image"}),
    "ANIMATIONS": ("06_google_flow_animations/prompts", {"image_to_video", "text_to_video"}),
}
NO_FLOW = {"REMOTION_GRAPHIC", "WHITEBOARD_TEXT", "CHART", "DIAGRAM", "MAP"}

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        err(f"{path.name}: cannot parse JSON ({e})")
        return None


def check_doc(path, doc, allowed, episode_id):
    n = path.name
    if not isinstance(doc, dict) or doc.get("schema_version") != "1.0":
        err(f"{n}: schema_version must be \"1.0\"")
    if not isinstance(doc, dict):
        return []
    if doc.get("episode_id") != episode_id:
        err(f"{n}: episode_id {doc.get('episode_id')!r} != episode config {episode_id!r}")
    jobs = doc.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        err(f"{n}: jobs must be a non-empty list")
        return []
    if "_B" in n and len(jobs) > MAX_JOBS:
        err(f"{n}: {len(jobs)} jobs exceeds the {MAX_JOBS} maximum")
    for j in jobs:
        jid = j.get("job_id", "?") if isinstance(j, dict) else "?"
        tag = f"{n}:{jid}"
        if not isinstance(j, dict):
            err(f"{n}: job is not an object")
            continue
        for k in REQUIRED:
            if k not in j:
                err(f"{tag}: missing {k}")
        if j.get("type") not in allowed:
            err(f"{tag}: type {j.get('type')!r} not allowed in this file (allowed {sorted(allowed)})")
        if not SCENE_RE.match(str(j.get("scene_id", ""))):
            err(f"{tag}: invalid scene_id")
        prompt = j.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            err(f"{tag}: empty prompt")
            prompt = ""
        elif "\n" in prompt:
            err(f"{tag}: prompt must be a single paragraph")
        if not SAFE_NAME_RE.match(str(j.get("output_name", ""))) or "." in str(j.get("output_name", "")):
            err(f"{tag}: unsafe output_name (no extension/path characters)")
        t = j.get("type")
        if t == "image":
            if j.get("source_image") is not None:
                err(f"{tag}: image job source_image must be null")
            if "duration_seconds" in j:
                err(f"{tag}: image job must not have duration_seconds")
            if not prompt.startswith("Still image."):
                err(f"{tag}: prompt must start with 'Still image.'")
        elif t in ("image_to_video", "text_to_video"):
            d = j.get("duration_seconds")
            if isinstance(d, bool) or not isinstance(d, (int, float)) or d <= 0 or d not in ALLOWED_VIDEO_DURATIONS:
                err(f"{tag}: duration_seconds {d!r} not in {sorted(ALLOWED_VIDEO_DURATIONS)}")
            if t == "image_to_video":
                if j.get("source_image") != j.get("scene_id"):
                    err(f"{tag}: source_image must reference the scene's approved still ({j.get('scene_id')})")
                m = DUR_RE.match(prompt)
                if not m:
                    err(f"{tag}: prompt lacks the mandatory 'Image-to-video. Use the approved still S### ... Duration: N seconds.' opening")
                else:
                    if m.group(1) != j.get("scene_id"):
                        err(f"{tag}: prompt scene {m.group(1)} != scene_id")
                    if isinstance(d, (int, float)) and float(m.group(2)) != float(d):
                        err(f"{tag}: prompt duration {m.group(2)} != duration_seconds {d}")
            elif j.get("source_image") is not None:
                err(f"{tag}: text_to_video source_image must be null")
    return [j for j in jobs if isinstance(j, dict)]


def main(folder):
    folder = Path(folder)
    cfg = folder / "production_status.json"
    try:
        episode_id = json.loads(cfg.read_text(encoding="utf-8"))["episode"]["id"]
    except (OSError, ValueError, KeyError):
        print(f"ERROR: cannot read episode id from {cfg}")
        return 1
    found, all_jobs, summary = False, {}, []
    for kind, (sub, allowed) in KINDS.items():
        d = folder / sub
        batches = sorted(d.glob(f"GOOGLE_FLOW_{kind}_B[0-9][0-9].json"))
        allf = d / f"GOOGLE_FLOW_{kind}_ALL.json"
        batch_jobs = []
        for p in batches:
            found = True
            doc = load(p)
            if doc is not None:
                batch_jobs += check_doc(p, doc, allowed, episode_id)
        if allf.exists():
            found = True
            doc = load(allf)
            if doc is not None:
                aj = check_doc(allf, doc, allowed, episode_id)
                if batches and aj != batch_jobs:
                    err(f"{allf.name}: contents differ from the combined batch files")
                if not batches:
                    batch_jobs = aj
        elif batches:
            err(f"{allf.name}: missing")
        if batches and len(batches) != -(-len(batch_jobs) // MAX_JOBS):
            err(f"{kind}: {len(batches)} batch files for {len(batch_jobs)} jobs (expected {-(-len(batch_jobs) // MAX_JOBS)} full batches)")
        ids = [j.get("job_id") for j in batch_jobs]
        if len(ids) != len(set(ids)):
            err(f"{kind}: duplicate job_id across batches")
        outs = [j.get("output_name") for j in batch_jobs]
        if len(outs) != len(set(outs)):
            err(f"{kind}: duplicate output_name")
        all_jobs[kind] = batch_jobs
        summary.append(f"{kind}: {len(batch_jobs)} jobs in {len(batches)} batches")
    if not found:
        print("No Flow JSON files found; nothing validated.")
        return 2

    # scene coverage against scene_timeline.csv
    tl = folder / "04_storyboard" / "scene_timeline.csv"
    if tl.exists() and any(all_jobs.values()):
        rows = list(csv.DictReader(tl.open(encoding="utf-8")))
        img = {j["scene_id"] for j in all_jobs["IMAGES"] if "scene_id" in j}
        vid = {j["scene_id"] for j in all_jobs["ANIMATIONS"] if "scene_id" in j}
        for r in rows:
            sid, vt = r["scene_id"], r["visual_type"]
            if vt in NO_FLOW and (sid in img or sid in vid):
                err(f"{sid}: Remotion-only scene ({vt}) must have no Flow job")
            if vt in ("STILL_IMAGE", "FLOW_ANIMATION") and all_jobs["IMAGES"] and sid not in img:
                err(f"{sid}: {vt} scene has no image job")
            if vt == "FLOW_ANIMATION" and all_jobs["ANIMATIONS"] and sid not in vid:
                err(f"{sid}: FLOW_ANIMATION scene has no animation job")
            if vt == "MIXED":
                warnings.append(f"{sid}: MIXED scene needs a manual Flow assignment check")
        known = {r["scene_id"] for r in rows}
        for s in (img | vid) - known:
            err(f"{s}: scene not in scene_timeline.csv")

    # dependencies: informational only, never "ready" without the approved file
    approved = folder / "05_google_flow_images" / "approved"
    img_scenes = {j.get("scene_id") for j in all_jobs["IMAGES"]}
    for j in all_jobs["ANIMATIONS"]:
        if j.get("type") != "image_to_video":
            continue
        sid = j.get("source_image")
        if sid not in img_scenes:
            err(f"{j.get('job_id')}: no image job produces source {sid}")
        if not list(approved.glob(f"{sid}.*")):
            warnings.append(f"{j.get('job_id')}: approved still {sid} not present yet (NOT READY to generate)")

    print(f"Episode {episode_id}: " + "; ".join(summary))
    for w in warnings:
        print("WARN:", w)
    for e in errors:
        print("ERROR:", e)
    print("PASS" if not errors else f"FAIL ({len(errors)} errors)")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
