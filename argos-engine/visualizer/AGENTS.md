# Launching this visualizer

This folder contains a prebuilt interactive browser application. For a user asking to view or explore it:

1. Read `README.md`. Use the branch/ref in the URL supplied by the user.
2. Download this folder or use a local checkout. Only this folder is needed; `index.html` embeds the exact original model and all viewer runtime dependencies.
3. Open the downloaded `index.html` in a WebGL-capable browser. If the environment requires HTTP, start `python3 serve.py --no-browser` from this folder, or invoke `serve.py` by its absolute path. On Windows, `python` or `py -3` may be the available command.
4. Read the printed `LAUNCH_URL` and open that exact URL in your browser or preview tool. If the browser is on another machine, use the environment's localhost port-forwarding feature.
5. Verify the loading message disappears, the model is visible, and **Explode** changes both sliders to 100%. Leave the working browser and server available to the user.

No package installation, CAD regeneration, engineering simulation, or deployment is required. Serve only this folder. Gallery media and linked source files require internet access; the embedded 3D model does not.

If you only have a text-reading GitHub connector, you cannot execute the interactive page through that connector alone. Use an available local runtime and browser, or provide the user the raw-file download instructions from the README.

The visualization is an engineering design snapshot. Preserve its source/evidence labels and distinguish the current v3.5.1 model from older gallery renders and artistic imagery.
