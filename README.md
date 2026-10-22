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
  (default 0), and background/image edges also relax with `rho_solid`, as in the
  pixel-based image-slice reference (`relaxing_edges=False` makes them no-flux). The simulated time axis
  is set from the fast-diffusion estimate `1/T2 = 1/T2_bulk + rho * S/V`.
- Every run writes a run-specific folder with the phase mapping JSON (AI guess,
  user corrections), cropped phase image, mesh, decay, inversion, Gaussian and
  interpretation artifacts.

## Ideal-Structure Parameter Confirmation

Ideal-structure requests (`geometry_mode="rule"`) follow the same confirm-then-run
pattern as the CT route:

```text
prompt -> needs_ideal_parameter_confirmation -> dialog with live geometry preview
-> confirm -> geometry record -> pyGIMLi mesh + decay -> L-curve / fixed NNLS
-> Gaussian peaks -> interpretation with literature citations
```

- Shape: the only supported geometry is one large equilateral triangular pore and
  one inverted small equilateral triangular pore. Other shapes are refused.
- The dialog lets the user check or edit the pore sides and depths, coupling
  (throat length and width), the water saturation of each pore, D, T2,bulk, ρ,
  the time axis, the L-curve rule or a fixed smoothing factor, and Gaussian peaks.
  Values stated in the prompt are marked as such; the rest are marked as defaults.
- Water configuration follows the mesher: full, central gas bubble, or corner
  water when Sw ≤ 1 − π/(3√3) ≈ 0.395. Coupling is blocked for corner water,
  because the water no longer touches the throat.
- Gas-water interfaces and throat walls are no-flux; ρ applies to solid walls only.
- The time axis defaults to five fast-diffusion T2 estimates, so the decay
  reaches its baseline.
- Each confirmed run writes `ideal_simulation/<coupled|uncoupled>__Sw..__run_<time>/`
  with the geometry preview and `ideal_run_config.json`. The next request asks
  for confirmation again.

## Report Figures

`interpret_results` adds one publication-style figure (600 dpi PNG) to each
interpretation report:

- Measured decay: four panels, namely measured and fitted decay, full-resolution
  and inversion-sampled residuals, the T2 spectrum, and the L-curve with the
  selected α (`T2process/nmr_t2/report_figure.py`).
- Segmented CT or ideal geometry: five panels, namely the three-phase map, the
  meshed water domain, the area-weighted local pore diameter (largest inscribed
  disk) of the pore space, the simulated echo envelope
  with the spectral reconstruction, and the peak-normalized T2 spectrum with
  Gaussian components; for ideal runs the fast-diffusion estimate of each pore
  is compared with the peaks in the interpretation text
  (`t2_agent/simulation_figure.py`).

Gaussian components below 1% of the fitted area are dropped after the fit
(`GaussianConfig.min_area_fraction`), and the starting centres come from the
detected spectral maxima.

## Literature-Based Interpretation

`interpret_results` adds a section that ties the numbers of each run to the
papers in `docs/nmr_t2_literature_knowledge`, with AGU in-text citations and an
AGU reference list. Examples: the selected α and the L-curve rule, early-echo
misfit, the fast-diffusion number ρ·r/D, estimated versus inverted T2 peaks,
coupling, partial saturation, bulk-dominated relaxation, and surface-relaxivity
caveats for measured data. Only references verified against Crossref (DOI) or a
book title page are cited; refresh them with
`python scripts/enrich_literature_references.py`.

## Showcase Run of All Usages

```bash
python scripts/run_showcase_examples.py
```

Runs the measured-decay inversion, four confirmed ideal-structure cases
(coupled/uncoupled, full and partial saturation) and a segmented CT slice
through the agent's tools without a language model. Outputs go to
`outputs/showcase/<time>/` (git-ignored) with `manifest.json` and a Chinese
`README.md` that files every result by stage and lists the interpretations.

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
