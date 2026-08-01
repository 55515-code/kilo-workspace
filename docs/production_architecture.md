# The Magician's Empire — Production Architecture

## Overview

"The Magician's Empire" is produced entirely through a procedural pipeline — Python scripts generate frames, composite layers of texture, typography, and symbolic imagery, and assemble the final output through FFmpeg. No traditional filming. No actors. No physical sets. Every frame is constructed.

This document defines the technical architecture, asset pipeline, render workflow, and quality control process for the production.

---

## Production Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.10+ | Primary production language |
| Image Generation | Pillow (PIL) | Frame composition, layer blending, text rendering |
| Image Processing | OpenCV (cv2) | Advanced image manipulation, filtering, transformations |
| Video Assembly | FFmpeg | Frame sequence to video encoding, audio sync, final output |
| Vector Graphics | cairosvg / svglib | SVG rendering for geometric elements, sacred geometry, mechanical diagrams |
| Font Rendering | Pillow + fonttools | Typography rendering, institutional and hand-drawn text |
| Texture Generation | NumPy + Pillow | Procedural texture generation (noise, grain, degradation) |
| Color Management | Pillow + custom LUTs | Color grading per movement, palette enforcement |

### Supporting Tools

| Tool | Purpose |
|------|---------|
| ImageMagick | Batch image processing, format conversion |
| ffprobe | Video metadata inspection, quality verification |
| pytest | Unit testing for frame generation functions |
| tqdm | Progress tracking for long render operations |

---

## Frame Generation Approach

### Pipeline Stages

```
1. PROCEDURAL SVG GENERATION
   ↓
2. SVG → PNG RASTERIZATION
   ↓
3. LAYER COMPOSITING (Pillow)
   ↓
4. TEXTURE OVERLAY
   ↓
5. TYPOGRAPHY RENDERING
   ↓
6. COLOR GRADING
   ↓
7. FRAME EXPORT (PNG sequence)
   ↓
8. FFmpeg ASSEMBLY (video + audio)
```

### Stage 1: Procedural SVG Generation

Geometric elements, mechanical diagrams, sacred geometry, architectural forms, and symbolic elements are generated as SVG. This provides:
- Resolution independence during composition
- Clean edges that can be rasterized at final output resolution
- Programmatic control over geometric parameters
- Easy modification and iteration

SVG elements are generated using Python string templates or the `svgwrite` library. Each element is parameterized — position, scale, rotation, color, opacity are all controlled by the production scripts.

### Stage 2: SVG → PNG Rasterization

SVG elements are rasterized to PNG at 1920×1080 using `cairosvg` or `svglib`. Rasterization happens at full resolution to preserve edge quality. Anti-aliasing is enabled.

### Stage 3: Layer Compositing

Each frame is composed from multiple layers, blended using Pillow's alpha compositing. A typical frame contains:

| Layer | Content | Blend Mode |
|-------|---------|------------|
| 0 | Background (solid color or gradient) | Normal |
| 1 | Environment (architecture, maze, factory) | Normal |
| 2 | Figures (silhouettes, masked figures) | Normal |
| 3 | Mechanical elements (gears, conveyor, strings) | Normal |
| 4 | Symbolic elements (masks, keys, curtains) | Normal |
| 5 | Texture overlay (xerox, charcoal, film grain) | Multiply / Overlay |
| 6 | Typography (institutional text, hand-drawn text) | Normal / Screen |
| 7 | Light effects (neon glow, exposure, firelight) | Screen / Add |
| 8 | Film damage (scratches, dust, light leaks) | Screen |

Layers are composited bottom-to-top. Each layer is a separate PNG file, enabling independent modification and re-rendering.

### Stage 4: Texture Overlay

Procedural textures are generated using NumPy noise functions and Pillow filters:

- **Xerox degradation:** High-contrast threshold + halftone simulation + paper grain
- **Charcoal/ink:** Perlin noise + directional blur + contrast enhancement
- **CRT interference:** Scan line generation + phosphor glow + signal noise
- **Scratched film:** Random vertical lines + dust particles + emulsion damage simulation
- **Film grain:** Gaussian noise at low opacity, frame-to-frame variation

Textures are generated per-frame with slight randomization to avoid visible repetition.

### Stage 5: Typography Rendering

Text is rendered using Pillow's `ImageDraw.text()` with custom fonts:

- **Institutional text:** Monospaced fonts (Courier, IBM Plex Mono) — clean, stamped, bureaucratic
- **Hand-drawn text:** Rough fonts or procedurally distorted text — charcoal, ink, scratched
- **Sacred text:** Ornamental fonts with geometric disruption overlays

Text position, size, rotation, and opacity are animated across frames using easing functions.

### Stage 6: Color Grading

Each movement has a defined color palette (see Visual Bible). Color grading is applied as a final pass:

- Palette enforcement: colors are mapped to the nearest palette entry
- Desaturation/saturation curves per movement
- Contrast adjustment per movement
- Optional LUT application for specific looks

### Stage 7: Frame Export

Each completed frame is exported as a PNG file in a numbered sequence:

```
frames/
  movement_01/
    frame_000001.png
    frame_000002.png
    ...
  movement_02/
    frame_000001.png
    ...
```

Frames are organized by movement for easy re-rendering and quality control.

### Stage 8: FFmpeg Assembly

The PNG sequence is assembled into final video using FFmpeg:

```bash
ffmpeg -framerate 24 -i frames/movement_%02d/frame_%06d.png \
       -i audio/the_magicians_empire.wav \
       -c:v libx264 -preset slow -crf 18 \
       -c:a aac -b:a 320k \
       -pix_fmt yuv420p \
       -shortest \
       output/the_magicians_empire.mp4
```

Multiple output formats may be generated:
- H.264 MP4 (primary delivery)
- ProRes 422 (high-quality master)
- WebM (web delivery)

---

## Resolution and Frame Rate

| Parameter | Value |
|-----------|-------|
| Resolution | 1920 × 1080 (Full HD) |
| Frame Rate | 24 fps (cinematic standard) |
| Color Space | sRGB (working), Rec. 709 (output) |
| Bit Depth | 8-bit per channel (output) |
| Total Frames | ~6,480 (for 4:30 duration) |
| Aspect Ratio | 16:9 |

---

## Asset Pipeline

### Asset Categories

#### Source Assets (External)

| Asset | Source | Format | Status |
|-------|--------|--------|--------|
| Audio track | Proton Drive | WAV (48kHz/24-bit) | Pending import |
| Reference images | Proton Drive | PNG/JPG | Pending import |
| Font files | Local / Google Fonts | TTF/OTF | Available |
| Texture source images | Proton Drive | PNG/TIFF | Pending import |

#### Generated Assets (Procedural)

| Asset | Generation Method | Storage |
|-------|------------------|---------|
| Architectural environments | SVG generation + rasterization | `assets/generated/environments/` |
| Figure silhouettes | SVG path generation | `assets/generated/figures/` |
| Masks | SVG circle/ellipse generation | `assets/generated/masks/` |
| Mechanical elements | SVG gear/lever/conveyor generation | `assets/generated/mechanical/` |
| Sacred geometry | SVG geometric path generation | `assets/generated/sacred_geometry/` |
| Maze layouts | Algorithmic generation (recursive backtracker) | `assets/generated/mazes/` |
| Procedural textures | NumPy noise + Pillow filters | `assets/generated/textures/` |
| Typography elements | Pillow text rendering | `assets/generated/typography/` |
| Neon glow effects | Gaussian blur + additive blending | `assets/generated/effects/` |
| Film damage overlays | Random line/particle generation | `assets/generated/film_damage/` |

### Asset Directory Structure

```
assets/
  source/
    audio/
    reference/
    fonts/
    textures/
  generated/
    environments/
    figures/
    masks/
    mechanical/
    sacred_geometry/
    mazes/
    textures/
    typography/
    effects/
    film_damage/
  cache/
    svg/
    png/
  output/
    frames/
    video/
```

---

## Render Workflow

### Development Render (Quick Preview)

For iteration and testing, a reduced-quality render is used:

| Parameter | Value |
|-----------|-------|
| Resolution | 960 × 540 (half) |
| Frame Rate | 12 fps (half) |
| Quality | Fast preview, minimal textures |
| Purpose | Timing, composition, motion verification |

```bash
python render.py --movement 1 --preview --output preview/
```

### Production Render (Final Quality)

Full-quality render for final output:

| Parameter | Value |
|-----------|-------|
| Resolution | 1920 × 1080 (full) |
| Frame Rate | 24 fps (full) |
| Quality | All textures, all layers, full color grading |
| Purpose | Final delivery |

```bash
python render.py --movement 1 --full --output frames/movement_01/
```

### Batch Render (All Movements)

Full production render across all movements:

```bash
python render.py --all --full --output frames/
python assemble.py --input frames/ --audio audio/source.wav --output output/
```

### Render Time Estimates

| Scope | Estimated Time |
|-------|---------------|
| Single frame (full quality) | ~2-5 seconds |
| Single movement (~30 seconds) | ~720 frames × 3s = ~36 minutes |
| Full video (4:30) | ~6,480 frames × 3s = ~5.4 hours |
| Preview render (full video) | ~6,480 frames × 0.5s = ~54 minutes |

Render times are estimates and depend on hardware, texture complexity, and layer count.

---

## Quality Control Process

### Per-Frame QC

Each generated frame passes through automated quality checks:

1. **Resolution check:** Verify 1920×1080
2. **Color space check:** Verify sRGB
3. **Blank frame check:** Detect accidentally blank or corrupted frames
4. **Palette compliance:** Verify colors are within movement palette tolerance
5. **Layer integrity:** Verify all expected layers are present and non-transparent

### Per-Movement QC

After rendering each movement:

1. **Frame count verification:** Ensure expected number of frames
2. **Sequence integrity:** Verify no missing or duplicate frames
3. **Visual review:** Scrub through rendered frames at playback speed
4. **Color consistency:** Verify color grading is consistent across movement
5. **Transition verification:** Check first and last frames match adjacent movement transitions

### Final Assembly QC

After FFmpeg assembly:

1. **Duration check:** Verify total duration matches target (~4:30)
2. **Audio sync:** Verify audio is synchronized with visual transitions
3. **Playback test:** Full playback at target resolution and frame rate
4. **File integrity:** Verify output file is not corrupted, plays on target platforms
5. **Bitrate check:** Verify output bitrate meets delivery requirements

### QC Script

```bash
python qc.py --input frames/ --movement all --report qc_report.html
```

The QC script generates an HTML report with:
- Thumbnail grid of every Nth frame
- Color histogram per movement
- Frame count and duration summary
- Any detected anomalies or warnings

---

## File Naming Conventions

### Frame Files

```
frame_{movement:02d}_{sequence:06d}.png
```

Example: `frame_01_000144.png` (Movement 1, frame 144)

### Asset Files

```
{category}_{description}_{variant:03d}.png
```

Example: `mask_white_featureless_001.png`

### Output Files

```
the_magicians_empire_{format}_{quality}.mp4
```

Examples:
- `the_magicians_empire_h264_final.mp4`
- `the_magicians_empire_prores_master.mov`
- `the_magicians_empire_webm_preview.webm`

---

## Error Handling and Recovery

### Render Interruption

If a render is interrupted:
- The render script tracks progress in a state file (`render_state.json`)
- Restarting the render resumes from the last completed frame
- Partial frames are detected and re-rendered

### Frame Corruption

If a frame is corrupted:
- The QC script flags the frame
- The render script can re-render individual frames by sequence number
- The assembly script skips corrupted frames and reports the gap

### Asset Missing

If a required asset is missing:
- The render script logs a warning and uses a placeholder (magenta fill)
- The QC report highlights frames with missing assets
- Production halts if critical assets are missing

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Storage | 50 GB free | 100+ GB free |
| GPU | Not required | Optional (for OpenCV acceleration) |

---

*This production architecture defines the technical framework for "The Magician's Empire." All code should be written to support this pipeline. All assets should be organized according to this structure. All renders should pass through this quality control process.*
