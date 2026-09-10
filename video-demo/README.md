# Book Genesis 5.0 — Demo Video

Remotion project for the Book Genesis 5.0 product demos. It contains a short product overview and a 48-second English installation walkthrough. The walkthrough separates observed installer output from the example host transcript so it can teach the workflow without pretending to be a provider benchmark.

## Quick start

```bash
npm install
npm run render
# output: out/demo.mp4
npm run render-install
# output: out/install-demo.mp4
```

## Preview in browser (Remotion Studio)

```bash
npm start
# opens http://localhost:3000 — scrub through all scenes interactively
```

## Render individual frames (still shots)

```bash
# Frame 0 — Scene 1: Title
npx remotion still src/index.ts BookGenesis50Demo --frame=0 out/frame-s1.png

# Installation walkthrough — install panel
npx remotion still src/index.ts BookGenesisInstallDemo --frame=270 out/install-cli.png

# Frame 120 — Scene 2: Idea typing (~4s in)
npx remotion still src/index.ts BookGenesis50Demo --frame=120 out/frame-s2.png

# Frame 270 — Scene 3: Pipeline (~9s in)
npx remotion still src/index.ts BookGenesis50Demo --frame=270 out/frame-s3.png

# Frame 600 — Scene 4: Score bar (~20s in)
npx remotion still src/index.ts BookGenesis50Demo --frame=600 out/frame-s4.png

# Frame 750 — Scene 5: Book ready (~25s in)
npx remotion still src/index.ts BookGenesis50Demo --frame=750 out/frame-s5.png

# Frame 870 — Scene 6: CTA (~29s in)
npx remotion still src/index.ts BookGenesis50Demo --frame=870 out/frame-s6.png
```

## Scene breakdown

| Scene | Frames | Time | Content |
|-------|--------|------|---------|
| S1 | 0–89 | 0–3s | Title fade-in: "Book Genesis 5.0" |
| S2 | 90–239 | 3–8s | Idea typing animation |
| S3 | 240–539 | 8–18s | Pipeline steps slide in |
| S4 | 540–719 | 18–24s | Editorial checkpoint and saved artifact |
| S5 | 720–839 | 24–28s | "Your next chapter is ready." |
| S6 | 840–959 | 28–32s | GitHub CTA |

## Installation walkthrough breakdown

| Section | Time | Content |
|---------|------|---------|
| Title | 0–4s | “Install once. Write with your agent.” |
| Install | 4–14s | `git clone` and the observed `runner/installer.py install claude` output |
| Verify | 14–22s | File-integrity verification and its model boundary |
| Use your host | 22–34s | English Claude Code/OpenCode/Codex prompt and saved project files |
| Resume | 34–43s | A fresh session reads `PROJECT_STATE.yaml` and continues |
| Open source | 43–48s | Repository, license, skills, and targets |

## Visual spec

- Background: `#0a0e1a`
- Purple accent: `#7c3aed` / `#a855f7`
- Green (pass): `#22c55e`
- Typography: system sans-serif for titles, monospace for code/terminals
- Feeling: flat, dark, dev-tool aesthetic — no marketing gradients

The installation walkthrough is composition `BookGenesisInstallDemo`, rendered at 1920×1080, 30fps, 48 seconds.

## Requirements

- Node 18+
- Remotion 4.x downloads Chrome Headless Shell automatically on first run (~85MB)
- FFmpeg must be on PATH for MP4 output (`ffmpeg -version` to check)
- No other system deps required
