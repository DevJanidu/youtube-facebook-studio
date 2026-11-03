# YouTube video production

The workspace is `video-production/`. Read `video-production/WORKFLOW.md` before doing any production work.

- When the user says **DONE**, run the checks in "Stage 2: DONE check" in that file, report whether the episode is ready, and stop.
- Do not create a storyboard until the user sends a separate storyboard prompt.
- Do not start Remotion graphics, sound design or editing until the user asks.
- For Remotion graphics, reuse the components in `video-production/shared/remotion-templates/` wherever they fit, following its `README.md`. Do not rebuild them, and keep existing components working when adding new ones.
- Editing uses the Master Episode Assembler in `video-production/shared/remotion-templates/`, following its `ASSEMBLER.md`. Run its `approve` and `export` commands only when the user says to.
- There are two production modes on one engine: a documentary (the default) and a vertical series cut into numbered parts. Follow `video-production/shared/remotion-templates/SERIES.md` for a series. Never export a series without being told which part, `--all-parts` or `--master`, and never approve a part for the user.
- **DONE means the same in both modes:** verify the finished script, narration, transcript and subtitles, report, and stop. Never plan parts, create a storyboard or start production after DONE.
- Never rewrite the final narration without the user's instruction, and never invent audio timings.
- Google Flow image/animation prompts are generated only after the storyboard stage and only when the user explicitly requests them, as separate schema v1.0 JSON files (max 10 jobs per batch, plus ALL files), following `video-production/shared/prompts/FLOW_JSON_GENERATION_STANDARD.md`. Validate with `video-production/tools/validate_flow_json.py`. Never modify Flow Queue Studio X. This does not change DONE.
