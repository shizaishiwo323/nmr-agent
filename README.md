# NMR Simulation and T2 Inversion Agent

A Streamlit-based AI workflow assistant for NMR 2D simulation and T2 inversion.
The app combines DeepSeek-guided conversation with a whitelisted local Python
tool layer for bundled ideal-triangle simulation, PNG phase-map simulation, pyGIMLi triangular meshing, T2
decay solving, data diagnosis, workbook repair, T2 inversion, visualization,
Gaussian peak decomposition, result interpretation, and report generation.

## Live App

[Open the deployed NMR Simulation and T2 Inversion Agent](https://t2-inversion-agent.streamlit.app/)

## What It Does

- Guides beginner users through T2 inversion choices in plain language.
- Detects flexible Excel layouts instead of assuming the first column is time.
- Repairs safe nonstandard workbooks into `time_ms + signal` format.
- Runs L-curve inversion when users do not know the smoothing factor.
- Runs fixed-regularization NNLS when users provide a smoothing factor.
- Generates plots, Gaussian peak fits, interpretation notes, reports, and a
  zip download for all outputs created during a task.
- Runs a first-version 2D NMR simulation workflow from the built-in ideal
  triangular-pore input or from uploaded PNG phase maps into the existing T2
  inversion tools.
- Runs the repository-bundled local NMR ideal-triangle demonstration for pyGIMLi mesh
  and T2 decay, while still sending the
  simulated decay into the existing fixed NNLS T2 inversion pipeline.
- Supports Chinese and English UI switching.

## 2D NMR Simulation Workflow

The app can also run a first-version 2D NMR simulation workflow:

```text
ideal triangular-pore input or red/yellow/white PNG -> pyGIMLi triangular mesh -> T2 decay solve -> T2 inversion
```

PNG phase maps must use:

- red for liquid/water pore space;
- yellow for solid matrix;
- white for outside/background.

White borders are cropped automatically. The ordinary first-version workflow
supports 2D T2 simulation only and does not perform CT segmentation, 3D
simulation, or D-T2. The local ideal-triangle demo is implemented inside this
repository; public deployments do not need a separately cloned NMR project or
Git submodule.

## Segmented CT TIF Workflow

Upload a segmented CT slice as a single-channel TIF/TIFF with one integer label
per phase (for example `0` outside, `102` water, `153` air, `255` solid):

```text
TIF labels -> background question (only if needed) -> draggable phase markers
-> parameter confirmation -> pyGIMLi mesh -> decay -> L-curve / fixed NNLS -> Gaussian peaks
```

- Images with two pixel values (solid + water) never trigger the background
  question. With three or four values the agent asks whether background pixels
  exist unless the prompt already says so.
- The AI first guess (background = border value, solid = largest phase, water =
  the wetting pore phase with more area and solid contact, air = the other pore
  phase) is shown as draggable markers on the real CT image. Dragging a marker
  onto another region reassigns that pixel value; phases swap automatically.
  A dropdown fallback and keyboard nudging are available.
- If the prompt does not give the CT resolution, simulation core parameters,
  the L-curve/smoothing-factor choice and the Gaussian choice, a confirmation
  dialog opens. Defaults: 1 um/pixel, L-curve on, Gaussian decomposition on.
- Boundaries: solid-water edges use `rho_solid`, air-water edges use `rho_gas`
  (default 0), and background/image edges are no-flux. The simulated time axis
  is set from the fast-diffusion estimate `1/T2 = 1/T2_bulk + rho * S/V`.
- Every run writes a run-specific folder with the phase mapping JSON (AI guess,
  user corrections), cropped phase image, mesh, decay, inversion, Gaussian and
  interpretation artifacts.

## Local Run

```bash
conda env create -f environment.docker.yml
conda activate t2agent
powershell -ExecutionPolicy Bypass -File scripts/run_streamlit_t2agent.ps1
```

The full 2D simulation workflow requires `pygimli` and uses the pyGIMLi
triangular mesh path. The no-upload/default simulation path uses the bundled
ideal triangular-pore input, not a generated PNG phase map. Do not use `base`
or a global `python -m streamlit` command. The startup script forces
`PYTHONNOUSERSITE=1`, verifies Python 3.11 plus `pygimli.meshtools`, and only
then starts Streamlit.
The project conda environment intentionally uses Python 3.11 with the main
scientific stack from conda-forge and the pyGIMLi wheel from PyPI; this is the
combination verified for the public Docker image.

Set a local DeepSeek key in `.streamlit/secrets.toml` or enter it in the web
page:

```toml
DEEPSEEK_API_KEY = "your-key"
```

Do not commit `.streamlit/secrets.toml`.

## Public Deployment

The pyGIMLi mesh workflow is best deployed from GitHub to a container-capable
public host such as Hugging Face Spaces Docker, Render, Railway, or another
Docker platform. This repository includes:

- `environment.docker.yml` for the full `t2agent` conda/Docker environment.
- `requirements.txt` for Streamlit Community Cloud's lightweight T2-processing deployment.
- `Dockerfile` for public deployment with the same conda environment.
- `scripts/check_t2agent_env.py` for dependency verification.

Pure pip-only hosts may fail to install pyGIMLi. For full public operation,
use the Dockerfile rather than a plain Streamlit Community Cloud build. The
Docker image supports the platform `PORT` environment variable and includes a
Streamlit health check. If no Cloud secret is configured, users can still
provide their own DeepSeek API key in the page.

## Safety Boundary

DeepSeek only chooses among whitelisted Python tools. It does not execute
arbitrary shell commands from user input.
