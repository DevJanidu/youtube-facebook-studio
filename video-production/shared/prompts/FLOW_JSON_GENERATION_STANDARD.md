# Google Flow JSON Generation Standard (permanent, all episodes)

Applies to every episode. Output is imported by the separate Chrome extension **Flow Queue Studio X** (never modified from this workspace). Schema is fixed at **v1.0**.

## When to run

Only **after the storyboard stage** and only when the user **explicitly requests** Flow image or animation prompts. Never as part of **DONE** (DONE only verifies script, narration, transcript and subtitles, then stops). Never start Flow automation, generate media, or assemble video.

## Inputs (read in this order; report anything missing, never invent)

1. `production_status.json` -> `episode.id` (use verbatim as `episode_id`; never a hardcoded example)
2. Approved `04_storyboard/storyboard.md` and `scene_timeline.csv` (`visual_type`, scene IDs)
3. Approved script and narration sections for each scene
4. Episode visual specs / character references / style guide in `04_storyboard/` and `asset_manifest.json`

Do not import character designs or styles from other episodes. Do not rewrite the script. Do not modify the storyboard.

Scene selection: `STILL_IMAGE`, `FLOW_ANIMATION` (and `MIXED` where the storyboard assigns a Flow still/animation) need Flow jobs. Scenes that are exclusively `REMOTION_GRAPHIC`, `WHITEBOARD_TEXT`, `CHART`, `DIAGRAM` or `MAP` get **no** job. Every Flow-assigned scene must be covered, however long the episode.

## Schema v1.0 (do not change, no extra required fields)

```json
{ "schema_version": "1.0", "episode_id": "<episode.id>", "jobs": [] }
```

Job fields: `job_id` (unique), `scene_id` (storyboard ID, e.g. S001, never renumbered), `type` (`image` | `image_to_video` | `text_to_video`), `prompt`, `source_image` (string or null), `output_name` (stem, no extension), `duration_seconds` (video jobs only, optional).

## Images and animations are never mixed

| | Still images | Animations |
| --- | --- | --- |
| `type` | `image` | `image_to_video` (or `text_to_video` only if explicitly required) |
| `source_image` | `null` | scene ID of approved still (`null` for text_to_video) |
| `duration_seconds` | omitted | required; allowed Flow value |
| `job_id` / `output_name` | `S001_IMG` / `S001` | `S001_VID` / `S001_A` |

Alternate versions: unique IDs/names such as `S001_V02` / `S001_A02`. Never convert image_to_video to text_to_video. Extension picks the mode from `type`.

## Batching and files

Max **10 jobs per file**. Batches keep original scene IDs, in storyboard order; batch numbers never rename scenes. Each file is an independently valid document.

| Folder | Files |
| --- | --- |
| `05_google_flow_images/prompts/` | `GOOGLE_FLOW_IMAGES_B01.json` ... `Bnn`, `GOOGLE_FLOW_IMAGES_ALL.json`, `FLOW_BATCH_INDEX.md` |
| `06_google_flow_animations/prompts/` | `GOOGLE_FLOW_ANIMATIONS_B01.json` ... `Bnn`, `GOOGLE_FLOW_ANIMATIONS_ALL.json` |

`FLOW_BATCH_INDEX.md` (human review only, saved in `05_google_flow_images/prompts/`, never inside JSON) lists: episode ID; total image jobs/batches; total animation jobs/batches; scene IDs per batch; expected output names; source-image dependencies; missing assets/unresolved info.

`*_ALL.json` is an **alternative** to the batches (same jobs). Import one or the other, never both, or jobs duplicate.

Never overwrite existing approved prompt files without permission. Existing `.md` prompt files stay untouched; JSON is the importable export.

## Still-image prompt (single paragraph)

Begins `Still image.` Then: composition, main subject, action/pose, background/environment, camera angle and framing, lighting, colors, expressions and clothing where relevant, key props, aspect ratio, the episode's visual style, negative constraints. No headings, scene numbers, bullets or explanations inside the string. No text overlays unless the storyboard requests them.

## Image-to-video prompt (mandatory opening)

`Image-to-video. Use the approved still S### as the first frame and visual reference. Duration: N seconds.` followed by only the animation: (1) specific subject/environment movement, (2) direction and speed, (3) camera behavior (locked by default), (4) pacing, (5) details that must remain unchanged, (6) negative constraints. Tailor to each scene; avoid unnecessary motion. `N` must equal `duration_seconds`.

Allowed durations are defined in one place, `ALLOWED_VIDEO_DURATIONS` in `tools/validate_flow_json.py` (currently 4, 6, 8, matching Veo in Flow). Confirm against Flow Queue Studio X's own schema if available; do not guess others.

## Source-image dependencies

`source_image` is only an identifier, not an attached image. An animation JSON may be exported before its still exists, but the job is **not ready** until the approved still exists in `05_google_flow_images/approved/` (and the user attaches/registry-resolves it in the extension). Do not mark dependencies ready, replace missing stills, or fall back to text_to_video. List unmet dependencies in the batch index.

## Validation (must run before reporting; never claim unrun checks)

```
python video-production/tools/validate_flow_json.py <episode_folder>
```

Checks: JSON syntax; schema_version "1.0"; episode_id equals production_status.json; required fields and types; valid `type`; unique `job_id`; scene IDs `S###`; non-empty prompts; safe `output_name` (no extension/path chars) unique per namespace; `Still image.` / `Image-to-video.` opening; source_image rules; allowed duration and prompt/`duration_seconds` match; no video jobs in image files and vice versa; <=10 jobs per batch; no duplicate jobs across batches; ALL file equals concatenated batches; image_to_video sources reference an image job/approved still (reported as dependency status, not "ready" unless the approved file exists). Scene coverage is checked against `scene_timeline.csv`.

## Procedure for a future episode

1. User sends the explicit Flow-prompt request. 2. Locate episode; confirm storyboard is approved and inputs exist (else report gaps and stop). 3. Draft image jobs, then animation jobs from the storyboard. 4. Write batches, ALL files, index. 5. Run the validator and report real results.
