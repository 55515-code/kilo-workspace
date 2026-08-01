# Handoff Prompt — Unblock "The Magician's Empire" Music-Video Production

Give the text below (everything under the horizontal rule) to the OpenClaw agent that has full
Kilo configuration access and full GitHub access. It is written to be executed, not discussed.

Context for whoever is pasting it: a prior Kilo cloud-agent session was hard-blocked from
producing the music video. The blockers were verified, not assumed:

- All shell execution is denied by a session-injected policy whose final rule is
  `{"permission":"bash","action":"deny","pattern":"*"}` (last match wins, so it overrides every
  preceding allow, including the per-command allow-list).
- Filesystem reads outside the session workspace are denied by an appended
  `{"permission":"*","action":"deny","pattern":"*"}`.
- The two Proton Drive share links are live but undownloadable without a POST-capable HTTP client
  and a crypto runtime (bcrypt-2y + SRP-6a + OpenPGP + AES-GCM).
- The workspace contains only an empty scaffold; there is no local copy of the audio or artwork.

---

# ROLE

You are a production-infrastructure engineer with full Kilo configuration access and full GitHub
access. Your job is **not** to make the music video. Your job is to remove every blocker so that a
follow-up Kilo agent can make it end-to-end without a single permission prompt, missing binary, or
missing source asset.

You are done only when you have produced verifiable proof — real command output, real file
checksums, real `ffprobe` dumps — committed to the repository.

# TARGET REPOSITORY / WORKSPACE

Repo: the repository currently checked out at
`/workspace/c4f0f93f-420c-45be-b382-0aad5ea19f06/sessions/agent_fc7e8e03-2901-4529-8794-5531ee7ea76b`
(scaffold contents: `README.md`, `Makefile`, `docker-compose.yml`, `.devcontainer/`,
`.github/workflows/{ci.yml,ai-agent.yml}`, `scripts/{setup,lint,test,dev}.sh`,
`examples/hello-world/`, `examples/api-service/`).

Resolve its GitHub remote with `git remote -v`. Do all work on a branch named
`infra/unblock-magicians-empire` and open a PR. Do not force-push `main`.

# BLOCKER 1 — Shell execution is force-denied

A previous agent's every shell attempt was rejected with this exact policy chain (abridged, note
the final rule):

```
[{"permission":"*","action":"allow","pattern":"*"},
 {"permission":"bash","pattern":"*","action":"ask"},
 {"permission":"bash","pattern":"cat *","action":"allow"}, ... ,
 {"permission":"bash","action":"allow","pattern":"*"},
 {"permission":"bash","action":"deny","pattern":"*"}]
```

Kilo evaluates permissions last-match-wins, and this `deny` is appended by the highest-precedence
layer, so a project-level `kilo.json` cannot override it.

Required actions:

1. Find where the deny is injected. Check, in order, and report the actual contents of each that
   exists:
   - managed/enterprise config: `/etc/kilo/kilo.json`, `/etc/kilo/kilo.jsonc`,
     `/etc/kilo/opencode.json`
   - global: `~/.config/kilo/kilo.json`, `~/.kilo/kilo.json`, `~/.kilocode/kilo.json`
   - env-injected: `KILO_CONFIG`, `KILO_CONFIG_DIR`, `KILO_CONFIG_CONTENT`
     (`printenv | grep -i kilo`)
   - agent-level `permission:` blocks in `**/{agent,agents}/**/*.md`
   - the cloud-agent runner definition: `.github/workflows/ai-agent.yml`, `.devcontainer/*`,
     `docker-compose.yml`, and any Kilo cloud/sandbox profile or org policy you can reach
   - `.kilocode/rules/*.md` and `AGENTS.md` for prose-level restrictions
2. Remove or override the blanket `bash` deny for this project so `bash` resolves to `allow`.
   Because last-match-wins, the allow must live in the layer that currently supplies the deny — do
   not just append an allow to a lower-precedence file and declare victory.
3. Do the same for `external_directory`. The follow-up agent needs read/write on the workspace plus
   `/tmp/**`, a scratch render dir, `~/.cache/**` (pip/npm/Blender/HuggingFace caches), and the
   font directories.
4. Set the project `kilo.json` to a permissive, explicit baseline and commit it:

```jsonc
{
  "$schema": "https://app.kilo.ai/config.json",
  "permission": {
    "bash": "allow",
    "edit": "allow",
    "read": "allow",
    "webfetch": "allow",
    "websearch": "allow",
    "task": "allow",
    "external_directory": "allow"
  }
}
```

5. **Prove it.** Run and paste raw output for:
   `uname -a; nproc; free -h; df -h .; whoami; printenv | grep -i -E 'kilo|proxy' | sort`

# BLOCKER 2 — The two-minute command cap

`.kilocode/rules/cloud-agent.md` instructs agents to cap every command at two minutes and to avoid
long repo-wide jobs. Video rendering, Blender builds, `pip install librosa`, and 4K encodes all
exceed that.

Required actions:

1. Rewrite that rule file (or add a project `AGENTS.md` section) to explicitly permit long-running
   media jobs: allow render/encode/install commands to run for at least 60 minutes, and require
   long renders to be launched as background processes with logs under `renders/logs/` that the
   agent tails.
2. Ensure the sandbox itself does not kill long processes. If there is a hard wall-clock or
   idle-timeout in the runner, raise it or document the exact ceiling in
   `docs/environment_capabilities.md`.
3. Confirm resources are sufficient for a 4K render: **≥ 40 GB free disk**, **≥ 8 GB RAM**,
   **≥ 4 vCPU**. If not, raise them, or record the true numbers and mark 1920×1080 as the sanctioned
   master resolution.

# BLOCKER 3 — Missing media toolchain

Install, verify, and pin the following. Prefer baking them into `.devcontainer/Dockerfile` **and**
making `scripts/setup.sh` idempotently install them, so the environment is reproducible rather than
hand-patched:

- `ffmpeg` + `ffprobe` — must include `libx264`, `libx265`, `aac`, and `prores_ks` or `dnxhd`
  (verify with `ffmpeg -encoders | grep -E 'x264|x265|prores|dnxhd|aac'`)
- `python3` ≥ 3.10 with a committed `requirements.txt`: `numpy`, `scipy`, `pillow`, `soundfile`,
  `librosa`, `aubio` (or `essentia`), `openai-whisper` or `faster-whisper`, `pyfoal`/`aeneas` or
  another forced aligner, `cairosvg`, `svgwrite`, `opencv-python-headless`, `matplotlib`,
  `imageio-ffmpeg`, `requests`, `bcrypt`, `pgpy` or `python-gnupg`, `srp` or `pysrp`,
  `cryptography`, `tqdm`
- `node` ≥ 20 + `npm`, with Remotion installable (`npx create-video --help` must resolve)
- `blender` ≥ 4.2 headless (`blender -b -v`) — install the real binary, not a stub
- `imagemagick` (`magick`/`convert`), `librsvg2-bin` (`rsvg-convert`), `potrace`, `inkscape`
- Fonts: `fonts-dejavu`, `fonts-liberation`, `fonts-inter`, `fonts-jetbrains-mono` or equivalent
  open faces; `fc-list | wc -l` must be > 50. Copy the chosen faces into `assets/fonts/` with their
  licenses so renders are reproducible.
- `git-lfs`, `jq`, `curl`, `wget`, `unzip`
- Optional but valuable: `nvidia-smi` — report whether a GPU exists; if yes, verify Blender sees it
  via CUDA/OptiX and that `ffmpeg` has `h264_nvenc`.

Verify outbound network for `pypi.org`, `registry.npmjs.org`, `github.com`, and
`drive-api.proton.me` with real status codes:
`for u in https://pypi.org/simple/ https://registry.npmjs.org/ https://github.com https://drive-api.proton.me; do curl -sS -o /dev/null -w "$u %{http_code}\n" "$u"; done`

Write every version string and every verdict to `docs/environment_capabilities.md` and commit it.

# BLOCKER 4 — The Proton Drive source assets

These are the authoritative inputs. They must end up on disk, unmodified, before the video agent
starts. Do not substitute anything.

- Audio master: `https://drive.proton.me/urls/XA248JXEJC#ERr0VGD3cKud`
- Source artwork: `https://drive.proton.me/urls/HJ9B06AF74#UlhAg0ZnPzCH`

Already-verified facts you can build on (obtained via plain GET, `Code: 1000` = success):

- `GET https://drive-api.proton.me/drive/urls/XA248JXEJC/info` →
  `UrlPasswordSalt: moW9oik4xkEBzw==`, `Version: 4`, `Flags: 2`, `IsDoc: false`, `DirectAccess: null`
- `GET https://drive-api.proton.me/drive/urls/HJ9B06AF74/info` →
  `UrlPasswordSalt: Xd26KqGfEtLg5w==`, `Version: 4`, `Flags: 2`
- `SRPSession` rotates per `/info` call, so the handshake must reuse the value from the same request.

Required actions — attempt in this order and stop at the first that yields real bytes:

1. **Implement `scripts/acquire_sources.py`** performing the full public-share flow:
   `GET /drive/urls/{token}/info` → derive the bcrypt-2y hash of the `#` fragment secret using
   `UrlPasswordSalt` → SRP-6a client proof against the returned `Modulus`/`ServerEphemeral` →
   `POST /drive/urls/{token}` with `ClientEphemeral`, `ClientProof`, `SRPSession` and the headers
   `x-pm-appversion: web-drive@5.0.0`, `x-pm-apiversion: 4`, `Accept: application/vnd.protonmail.v1+json`
   → `GET .../children` → decrypt share/node keys with OpenPGP → fetch content blocks → AES-GCM
   decrypt → reassemble. Verify the server proof; do not skip validation.
2. If a maintained third-party downloader exists on PyPI/npm/crates that handles Proton public
   shares, use it and pin the version.
3. Headless browser fallback: `pip install playwright && playwright install chromium`, drive the
   share URL with the fragment secret, let Proton's own web client do the crypto, and capture the
   download to disk. Confirm the saved file is not an HTML error page (`file` + size + magic bytes).
4. If and only if all automated routes fail, mirror the two files into the GitHub repo yourself via
   git-lfs or a private GitHub Release, and record the exact upload provenance. Then have
   `scripts/acquire_sources.py` fall back to that mirror. **Never** commit a placeholder.

Then:

- Save originals read-only to `assets/source/audio/` and `assets/source/visual/`
  (`chmod 444`), and record `sha256sum` for each in `docs/asset_inventory.md`.
- Run and commit the raw output of
  `ffprobe -v error -show_format -show_streams -of json <audio>` — duration, codec, container,
  sample rate, channel layout, bit depth — plus
  `ffmpeg -i <audio> -af ebur128=peak=true -f null -` for peak/integrated loudness.
- Run and commit `identify -verbose <image> | head -60` — dimensions, format, colorspace, bit depth.
- Confirm the audio is a real full-length song (not a fragment) and the image is the
  highest-resolution version available. State both durations/dimensions explicitly.

# BLOCKER 5 — Project structure, build commands, and GitHub hygiene

1. Create the full tree with `.gitkeep` files: `analysis/`, `assets/{source/{audio,visual},generated,textures,vectors,models,fonts}/`, `captions/`, `docs/`, `review/{keyframes,contact_sheets}/`, `scripts/`, `scenes/`, `src/`, `renders/{proxy,scenes,final,logs}/`, `deliverables/social/`, `tests/`.
2. Add deterministic build entry points that exist and run (they may currently be thin wrappers, but
   each must exit 0 and print what it will do):
   `make acquire`, `make analyze`, `make animatic`, `make render`, `make validate`, and matching
   `scripts/*.py`. Wire them into the existing `Makefile` rather than replacing it.
3. `.gitignore`: exclude `renders/**` and large intermediates; track `deliverables/**` via git-lfs
   (`git lfs track "*.mp4" "*.mov" "*.wav" "*.flac" "*.png"`). Commit `.gitattributes`.
4. Confirm GitHub push works: create the branch, commit, push, open the PR, and report the PR URL.
   If a GitHub Actions workflow would be triggered by media commits, make sure it does not fail the
   PR — adjust `.github/workflows/ci.yml` paths-ignore as needed.
5. Check for existing secrets/integrations the video agent could use (image/audio generation APIs,
   MCP servers). List what is configured in `docs/environment_capabilities.md`; do not print secret
   values.

# ACCEPTANCE CRITERIA — do not report success without these

Commit `docs/unblock_verification.md` containing **raw, unedited command output** proving:

1. A shell command runs without any permission prompt or denial.
2. `ffmpeg -version`, `ffprobe -version`, `python3 -VV`, `node -v`, `blender -b -v`,
   `magick -version`, `rsvg-convert -v`, `fc-list | wc -l`.
3. `python3 -c "import numpy, librosa, soundfile, PIL, cairosvg, cv2; print('py-ok')"` prints `py-ok`.
4. A real end-to-end render smoke test: generate a 5-second 1920×1080 24 fps clip from a
   procedurally drawn SVG/PNG sequence, mux it with a 5-second slice of the acquired audio, then
   `ffprobe` it and extract a frame to PNG. Paste the ffprobe JSON and confirm the PNG is
   non-blank (report its mean pixel value). Store it at `tests/smoke/smoke.mp4`.
5. Both Proton source files exist on disk with sizes, sha256 sums, `ffprobe`/`identify` output.
6. Free disk, RAM, vCPU count, and GPU verdict.
7. The wall-clock ceiling for a single command, and confirmation that a >5-minute background job
   completed successfully.
8. The PR URL.

If any single item cannot be satisfied, say so explicitly, name the exact mechanism that blocks it,
and state what escalation is required — an org policy change, a bigger runner, a different sandbox
image, or the user hand-uploading a file. Do not paper over it and do not fabricate output.

# FINAL DELIVERABLE

Reply with: the PR URL, the branch name, the capability table, the two source-asset checksums and
their probe summaries, the smoke-test result, and a single explicit sentence stating whether a
follow-up Kilo agent can now execute the complete music-video production — acquisition, audio
analysis, lyric alignment, animatic, 4K render, frame-level QC, captions, thumbnail, 9:16
derivatives, and decode validation — with zero remaining blockers.
