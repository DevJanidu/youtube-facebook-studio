# YouTube video production

The workspace is `video-production/`. Read `video-production/WORKFLOW.md` before doing any production work.

- When the user says **DONE**, run the checks in "Stage 2: DONE check" in that file, report whether the episode is ready, and stop.
- Do not create a storyboard until the user sends a separate storyboard prompt.
- Do not start Remotion graphics, sound design or editing until the user asks.
- For Remotion graphics, reuse the components in `video-production/shared/remotion-templates/` wherever they fit, following its `README.md`. Do not rebuild them, and keep existing components working when adding new ones.
- Editing uses the Master Episode Assembler in `video-production/shared/remotion-templates/`, following its `ASSEMBLER.md`. Run its `approve` and `export` commands only when the user says to.
- Never rewrite the final narration without the user's instruction, and never invent audio timings.
