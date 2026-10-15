# Open the ARGOS H1 visualizer

This is the ready-to-run interactive explorer for `argos-engine/`. It contains the original v3.5.1 CAD assembly, assembly/disassembly sliders, cutaway and subsystem views, part details, a folder map, and a searchable catalog of 1,097 visual and design files.

**No npm install, CAD software, solver, build step, or Python packages are required.**

## Ask an AI to open it

Give a browser-capable AI this folder's GitHub URL and the following prompt:

> Open the ARGOS H1 visualizer in this repository. Read `argos-engine/visualizer/README.md` and `argos-engine/visualizer/AGENTS.md`, download or clone the visualizer from the linked branch, and open the working interactive page in your browser. If you need a local server, run `python3 argos-engine/visualizer/serve.py --no-browser` (use `python` or `py -3` on Windows) and open the URL it prints. Verify that the model appears and the Explode button works. Keep the browser and server open so I can explore it. There is no need to install packages, rebuild CAD, or run simulations.

Use the branch in the supplied GitHub link. The visualizer is on `codex/argos-engine-visualizer` until its pull request is merged.

## Option 1: download and open one file

Download [`index.html`](index.html) using GitHub's **Download raw file** action, then open the downloaded file in Chrome, Edge, Firefox, or another browser with WebGL support.

The file includes the 3D model, renderer, metadata, controls, and styles. GitHub's file-preview page displays source code and does not execute the visualizer. A GitHub connector that can only read text cannot display an interactive page; the AI also needs a local filesystem and browser, or a browser preview environment.

## Option 2: launch from a clone

From the repository root:

```sh
python3 argos-engine/visualizer/serve.py
```

On Windows:

```powershell
py -3 argos-engine/visualizer/serve.py
```

The launcher opens the page in your default browser and prints `LAUNCH_URL=...`. It uses an available local port rather than assuming a particular port is free. Press Ctrl+C in that terminal to stop it.

For an AI-managed browser, suppress the default browser window and open the printed URL with the AI's browser tool:

```sh
python3 argos-engine/visualizer/serve.py --no-browser
```

Python 3.9 or newer is sufficient. The launcher uses only the standard library, serves this folder on `127.0.0.1`, and works regardless of the terminal's current directory. You can also run `serve.py --check` to verify the embedded model and manifest without starting a server. `--port 8765` selects a specific port if needed.

### Download only the viewer with Git

```sh
git clone --depth 1 --filter=blob:none --sparse --branch codex/argos-engine-visualizer https://github.com/gasparamiune/p1-propulsion.git
cd p1-propulsion
git sparse-checkout set argos-engine/visualizer
python3 argos-engine/visualizer/serve.py
```

The folder is self-contained. It does not depend on another checkout, a Windows-specific path, or a running service on the author's computer.

## What needs the internet

The assembly and explanations work locally. Gallery images, videos, PDFs, CAD downloads, and GitHub source links load from the public repository on demand. An optional Google Fonts stylesheet has system-font fallbacks.

All engineering source links are pinned to commit `0efd80709a0c65e677150764a31c47680ee86f0b`. The viewer is a documented snapshot, so later repository changes do not silently change the model or evidence. Older renders, working material, and artistic plume illustrations are identified separately in the library. The catalog includes historical revisions and duplicate files.

## Design context

The 148 modeled instances retain all 248,662 source triangles from `03-cad/v3.5.1/assembly/ENGINE_v3.5.1_neutral.glb`. The tank and airframe are absent. Explosion offsets explain component relationships; they are not a prescribed assembly or maintenance sequence.

The engine is an unbuilt design, simulation and review draft. No part has been built, fired, or measured. The explorer carries the repository's evidence labels and documented open engineering issues.

`provenance.json` records the source snapshot and hashes. `THIRD_PARTY_NOTICES.txt` contains the renderer's license. The distributed `index.html` is prebuilt; ordinary viewing does not rebuild or modify engineering files.
