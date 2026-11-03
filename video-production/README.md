# Video Production Workspace

A reusable workspace for producing animated educational YouTube videos. Each episode gets its own folder, with the same structure and tracking.

See [WORKFLOW.md](WORKFLOW.md) for the full process and the rules for each stage.

## Create an episode

Run this from the `video-production` folder. It needs Python 3 and nothing else.

```text
python tools/create_episode.py --id 001 --title "Example Topic"
```

This creates `episodes/001_example-topic/` with all subfolders and blank templates. Each episode ID can be used only once, so an existing episode cannot be overwritten.

For a vertical series, add `--mode series`. It sets a 9:16 frame and adds `series_manifest.json`. The documentary is the default. See `shared/remotion-templates/SERIES.md`.

## Add your completed files

| File | Folder |
| --- | --- |
| Final script | `02_script/` |
| Narration audio | `03_narration/audio/` |
| Transcript | `03_narration/transcript/` |
| Subtitles (SRT) | `03_narration/subtitles/` |

Then tell Claude Code **DONE**. Claude Code checks the files and reports whether the episode is ready for a storyboard. It does not create the storyboard until you send a separate prompt.

## Workspace layout

| Path | Purpose |
| --- | --- |
| `shared/sound-effects/` | Sound effect library for all episodes |
| `shared/music/` | Background music for all episodes |
| `shared/remotion-templates/` | Reusable motion graphics library. See its `README.md` |
| `shared/prompts/` | Reusable prompts |
| `templates/` | Blank files copied into each new episode |
| `tools/create_episode.py` | Episode generator |
| `episodes/` | One folder per episode |

## Episode layout

| Folder | Contents |
| --- | --- |
| `01_research/` | Optional research notes |
| `02_script/` | Final script |
| `03_narration/` | Audio, transcript and subtitles |
| `04_storyboard/` | `storyboard.md`, `scene_timeline.csv` and `asset_manifest.json` |
| `05_google_flow_images/` | Still image prompts, generated images and approved images |
| `06_google_flow_animations/` | Image-to-video prompts, generated clips and approved clips |
| `07_remotion/` | Motion graphics source, renders and previews |
| `08_sound_design/` | Sound cues, effects and music used in the episode |
| `09_editing/` | Edit projects, review previews and QA notes |
| `10_final_export/` | Final video, thumbnail and metadata |
| `production_status.json` | Status of the 12 production stages |
