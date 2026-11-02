# Production Workflow

## Overview

1. I complete my script outside the system.
2. I generate my ElevenLabs narration.
3. I prepare my transcript and subtitles.
4. I create an episode folder.
5. I place the completed files inside that folder.
6. I tell Claude Code **DONE**.
7. Claude Code verifies those files and reports readiness.
8. I send a separate storyboard prompt.
9. Claude Opus creates a narration-synchronized storyboard.
10. I generate Google Flow still images.
11. I generate selected Google Flow animations.
12. Claude Code creates Remotion motion graphics.
13. Claude Code handles sound design and editing when instructed.
14. I review the video.
15. The final version is exported.

## Rules that apply to every stage

- The final script and narration are the source of truth. Never rewrite them without the user's instruction.
- The script is finalized before it arrives here. Do not research the topic again, write a new script or ask for script approval.
- There is one narrator voice.
- Do not generate voiceovers, transcripts or subtitles unless the user explicitly asks.
- Do not generate images or animations automatically.
- Do not invent a project name, character names, a mascot design or character references. The user supplies these.
- Never treat unfinished assets as completed.
- Start each stage only when the conditions below say so. Finishing one stage does not start the next.

## Stage 1: Add the completed files (user)

Create the episode from the `video-production` folder:

```text
python tools/create_episode.py --id 001 --title "Example Topic"
```

Then place the completed files:

| File | Folder |
| --- | --- |
| Final script | `02_script/` |
| Narration audio | `03_narration/audio/` |
| Transcript | `03_narration/transcript/` |
| Subtitles (SRT) | `03_narration/subtitles/` |

Then tell Claude Code **DONE**.

## Stage 2: DONE check (Claude Code)

When the user says DONE:

1. Locate the current episode folder. If more than one episode could be meant, ask which one.
2. Check which completed files were provided.
3. Verify that the audio, script, transcript and subtitles are readable.
4. Measure the actual audio duration with `ffprobe`.
5. Check the subtitle timestamps and whether they match the narration:
   - Cues are in order, each one starts before it ends, and cues do not overlap.
   - The last cue ends close to the end of the audio, and no cue runs past it.
   - Subtitle text agrees with the transcript and the script.
   - Subtitle timing agrees with the audio itself, for example by comparing cue gaps with silences found by FFmpeg's `silencedetect`.
6. Identify any missing files or timing mismatches.
7. Report whether the episode is ready for storyboard creation.

The report must say which checks ran and which could not. It must not claim word-level sync unless the audio was actually aligned against the text.

Update stages 1 to 4 in `production_status.json`. Change no other files, and do not repair or replace the user's files.

**Then stop. Do not create the storyboard until the user sends a separate prompt.**

## Stage 3: Storyboard (Claude Opus)

**Starts only after the user's separate storyboard prompt.**

Before planning any scenes:

1. Read the entire finalized script.
2. Inspect the narration audio.
3. Read the complete transcript.
4. Parse the SRT subtitles and timestamps.
5. Determine the actual narration duration.
6. Align narration sentences with their correct audio timings.
7. Understand the story, explanations, emotional changes and important visual moments.

If subtitle timestamps are inaccurate or too coarse, use available audio-alignment tools to produce more accurate timings. Do not invent exact timings. If accurate timing cannot be established, report it instead of guessing.

The main job is to decide **what the viewer should see at every moment while listening to the narration**.

Number the scenes S001, S002, S003 and so on. Use as many scenes as the narration needs. Each scene must contain:

- Scene number
- Exact start timestamp
- Exact end timestamp
- Duration
- Matching narration text
- Purpose of the scene
- What should appear visually
- Character requirements, if applicable
- Contextually appropriate clothing, if applicable
- Recommended visual format
- Image or animation requirements
- Remotion graphics requirements
- On-screen text, if necessary
- Sound effect suggestions
- Transition suggestions

Write the results to these files in `04_storyboard/`:

| File | Contents |
| --- | --- |
| `storyboard.md` | The full scene descriptions |
| `scene_timeline.csv` | One row per scene |
| `asset_manifest.json` | The assets each scene needs |

The storyboard must also:

- Follow the final narration, not the other way around.
- Match the visuals to the exact spoken explanation.
- Avoid unnecessary visual repetition.
- Balance still images, Google Flow animations, Remotion graphics, whiteboard text, charts, diagrams and maps.
- Use context-specific characters and clothing when needed.

The user then reviews the storyboard. Later stages use the approved version.

### Timeline format

| Column | Format |
| --- | --- |
| `scene_id` | `S001` |
| `start_time`, `end_time` | `HH:MM:SS.mmm` |
| `duration` | Seconds, such as `4.250` |
| `visual_type` | `STILL_IMAGE`, `FLOW_ANIMATION`, `REMOTION_GRAPHIC`, `WHITEBOARD_TEXT`, `CHART`, `DIAGRAM`, `MAP` or `MIXED` |
| `image_asset`, `animation_asset`, `remotion_asset` | Path relative to the episode folder, or blank if not needed |
| `status` | One of the five production statuses |

## Stage 4: Still images (user, Google Flow)

The user generates still images from the approved storyboard. Claude Code does not create images automatically.

| Item | Location |
| --- | --- |
| Prompts | `05_google_flow_images/prompts/S001.md` |
| Generated images | `05_google_flow_images/generated/S001_v1.png` |
| Approved images | `05_google_flow_images/approved/S001.png` |

## Stage 5: Scene animation (user, Google Flow image-to-video)

Selected approved still images are animated in Google Flow. Use this for character movements, physical actions, environmental movement, cinematic storytelling and important visual moments. Only animate scenes that genuinely benefit from motion.

| Item | Location |
| --- | --- |
| Prompts | `06_google_flow_animations/prompts/S001.md` |
| Generated clips | `06_google_flow_animations/generated/S001_v1.mp4` |
| Approved clips | `06_google_flow_animations/approved/S001.mp4` |

## Stage 6: Motion graphics (Claude Code, Remotion)

**Starts when the user instructs it.**

Claude Code creates programmatic motion graphics such as charts, diagrams, maps, timelines, whiteboard text, comparison graphics, scientific explanations and educational animations. Work goes in `07_remotion/`, and reusable components go in `shared/remotion-templates/`.

Use the existing components in `shared/remotion-templates/` wherever they suit a scene, and do not rebuild those animations. Its `README.md` explains how to reuse them and how to add new ones. Time every graphic from the storyboard's real narration timestamps. New components must not change or remove existing ones.

Google Flow handles image-to-video scene animations. Remotion handles code-generated motion graphics. These are separate production processes.

## Stage 7: Sound design (Claude Code)

**Starts when the user instructs it.**

Using the library in `shared/`, add sound effects, background music, environmental ambience, cartoon reactions, cinematic sounds and appropriate transitions. Sound effects must match the visual actions and narration timing. Keep the narration clear and understandable.

Cue lists go in `08_sound_design/cues/`. Copies of the effects and music used in the episode go in `08_sound_design/effects/` and `08_sound_design/music/`.

## Stage 8: Editing (Claude Code, Remotion, FFmpeg)

**Starts only when the user explicitly requests it.**

Claude Code helps to:

- Assemble images and animations
- Integrate Remotion graphics
- Synchronize visuals with narration
- Add sound effects and background music
- Prepare review previews
- Check for missing scenes and synchronization
- Prepare the final video

Edit projects go in `09_editing/projects/`, review previews in `09_editing/previews/` and check results in `09_editing/qa/`.

Editing uses the Master Episode Assembler. See `shared/remotion-templates/ASSEMBLER.md` for its commands and file formats. No other video editor is needed.

Claude Code runs `approve` and `export` only when the user says to. The final video renders only after the user approves a review preview.

## Stage 9: Review and final export

The user reviews the video. The approved version is exported to `10_final_export/`, with the thumbnail and metadata in their own subfolders.

## Production tracking

Each episode's `production_status.json` tracks 12 stages:

1. Script and source files received
2. ElevenLabs audio received
3. Transcript and subtitles received
4. Audio timing verified
5. Storyboard generated
6. Storyboard reviewed
7. Google Flow images
8. Google Flow animations
9. Remotion graphics
10. Sound design
11. Editing
12. Final export

Each stage has one of these statuses:

| Status | Meaning |
| --- | --- |
| `NOT_STARTED` | No work has begun |
| `IN_PROGRESS` | Work is under way |
| `NEEDS_REVIEW` | Work is ready for the user to review |
| `COMPLETED` | Finished, with evidence recorded |
| `BLOCKED` | Cannot continue; the reason is in `notes` |

Do not mark a stage `COMPLETED` merely because a directory exists. List the actual files or checks that prove it in the stage's `evidence` field.
