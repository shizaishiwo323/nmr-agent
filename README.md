# NMR Simulation and T2 Inversion Agent

A Streamlit-based AI workflow assistant for NMR 2D simulation and T2 inversion.
The app combines a conversation with a large language model (LLM), accessed
through any OpenAI-compatible chat-completions API, with a whitelisted local Python
tool layer for bundled ideal-triangle simulation, PNG phase-map simulation, pyGIMLi triangular meshing, T2
decay solving, data diagnosis, workbook repair, T2 inversion, visualization,
Gaussian peak decomposition, result interpretation, and report generation.

This repository accompanies the manuscript by Y. Zhang, B. Wang and C. Zhang,
"An AI-agent framework for physics-based NMR interpretation in unsaturated
geomaterials" (submitted to *Computers & Geosciences*).

## Live App

[Open the deployed NMR Simulation and T2 Inversion Agent](https://nmr-agent.streamlit.app/)

The hosted app has no API key of its own. Open **API settings**, choose a
provider and paste your own key (see below). The key stays in your browser
session and is not stored by the app. The app sleeps when idle, so the first
visit can take a minute to wake up.

## How to Cite

If you use this code, the web app or results produced with them, please cite
the following publications:

- Wang, B., Zhou, J., Rembert, F., Heck, L., Bate, B., & Zhang, C. (2026).
  Tracking spatiotemporal mineral dissolution through quantitative nuclear
  magnetic resonance signatures. *Geophysical Research Letters*, 53(14).
  https://doi.org/10.1029/2026gl124613
- Zhou, J., & Zhang, C. (2025). How does pore structure affect the NMR
  relaxation in unsaturated porous media: A simulation study. *Water Resources
  Research*, 61(2). https://doi.org/10.1029/2024wr038139
- Zhou, J., Schröer, L., Cnudde, V., & Zhang, C. (2026). How does fluid exchange
  between pores in unsaturated porous media? *Geophysical Research Letters*,
  53(5). https://doi.org/10.1029/2025gl120450

## Language Models

The agent calls the model through the OpenAI Python client and the standard
chat-completions endpoint with function calling, so any compatible provider can
be used:

| Provider | Base URL | Model |
|---|---|---|
| DeepSeek (used in the paper) | `https://api.deepseek.com` | `deepseek-v4-pro` (default) or `deepseek-v4-flash`; thinking mode optional |
| OpenAI | `https://api.openai.com/v1` | any chat model with function calling (default field value `gpt-4.1`) |
| Custom | your endpoint | any OpenAI-compatible model with function calling |

The results in the paper were produced with DeepSeek-V4-Pro (thinking mode on,
temperature 0.2). Other models choose tools differently, so their replies can
differ. The tools and solvers are the same, whichever model is used. The automated tests check the
provider layer with a mock client; they do not call a live model.

A key is needed for the chat, which drives all workflows. The key only pays
for the model's replies: meshing, forward modelling, inversion and
interpretation run inside the app.

## What It Does

- Guides beginner users through T2 inversion choices in plain language.
- Detects flexible Excel layouts instead of assuming the first column is time.
- Repairs safe nonstandard workbooks into `time_ms + signal` format.
- Runs L-curve inversion when users do not know the smoothing factor; the
  default selection is the slope-of-the-L-curve criterion of Zou et al. (2016),
  and maximum curvature (Hansen, 1992) is available for noise-free simulations.
- Runs fixed-regularization NNLS when users provide a smoothing factor.
- Generates plots, Gaussian peak fits, interpretation notes, reports, and a
  zip download for all outputs created during a task.
- Runs a first-version 2D NMR simulation workflow from the built-in ideal
  triangular-pore input or from uploaded PNG phase maps into the existing T2
  inversion tools.
- Runs the repository-bundled local NMR ideal-triangle demonstration for pyGIMLi mesh
  and T2 decay, while still sending the
  simulated decay into the existing fixed NNLS T2 inversion pipeline.
- English user interface by default, with a Chinese option.

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
  reaches its baseline; the implicit-Euler step is kept below 1/40 of the
  shortest estimate (T2 bias under about 1.3%).
- Each confirmed run writes `ideal_simulation/<coupled|uncoupled>__Sw..__run_<time>/`
  with the geometry preview and `ideal_run_config.json`. The next request asks
  for confirmation again.

## Paper Cases (Sections 3 and 5 of the manuscript)

`t2_agent/paper_sim/` contains the forward and inverse calculations of the
controlled cases and the pixel-grid CT solver used in the manuscript, with the
Table 1 settings as defaults. The agent calls them through five tools; each run
writes a manuscript-style figure (PNG 600 dpi and PDF), a workbook and a JSON
summary.

| Tool | Case | Responses |
|---|---|---|
| `simulate_pore_shapes` | Equal-area circle, equilateral and 30°-60°-90° triangles (Fig. 4) | T2, D–T2, T1–T2 |
| `simulate_saturation_series` | Corner water in an equilateral pore at several saturations (Fig. 6) | T2, D–T2, T1–T2 |
| `simulate_contact_angle_series` | Contact angles at equal water area (Fig. 7) | T2, D–T2, T1–T2 |
| `simulate_dual_pore_exchange` | Two pores, effective compartment exchange k_ex = D_eff / l_c² (Fig. 5) | T2 |
| `simulate_ct_slice_pixel_grid` | Finite-volume solution on the CT pixel grid, L-curve inversion (Fig. 9) | T2 |

T2 uses consistent-mass FEM on pyGIMLi meshes with a generalized Lanczos
evaluation; D–T2 (narrow-pulse PFG) and T1–T2 (saturation recovery) propagate
the magnetization with Crank–Nicolson steps; surface relaxation acts on
solid–water edges only. `tests/test_paper_sim.py` checks the ported
calculations against values in the manuscript.

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

The full rule set (20 rules), the conditions under which each rule is applied
and the 21 references it cites are listed in
[`docs/interpretation_rules.md`](docs/interpretation_rules.md); the literature
library (64 papers) is in `docs/nmr_t2_literature_knowledge/`.

`interpret_results` adds a section that ties the numbers of each run to the
papers in `docs/nmr_t2_literature_knowledge`, with AGU in-text citations and an
AGU reference list. Each statement leads with what the number means for the
sample and is emitted only when the agent has computed the quantity it rests on:

- Measured decay of a soil or organic-rich sample (named in the request or in
  `sample_description`): water-state classes (< 60 ms, 60–300 ms, > 300 ms;
  Bayer et al., 2010), the share relaxing slower than 1 s against the about 2 s
  of extracted pore water, two Gaussian water populations, and the bound-water
  lower bound set by the first echo.
- Ideal triangle pair: peaks against the per-pore fast-diffusion estimates
  without coupling; with a throat, the fast-exchange limit, the exchange time and
  the small-pore water merged into one peak; under partial saturation, the
  capacity check of Zhou and Zhang (2025).
- Segmented CT slice: the harmonic-mean T2 against the meshed S/V (exact for the
  initial decay rate), the peak bias for ρ calibration, pixel versus mesh S/V,
  bulk-relaxation share, wetted-wall fraction, spectral area above T2,bulk, and
  unresolved Gaussian components.

Only references verified against Crossref (DOI) or a book title page are cited;
refresh them with `python scripts/enrich_literature_references.py`. The web
LLM is instructed to lead its reply with these findings, keep their numbers and
citations, and add no caveats that the findings do not state. When the six tool
rounds are spent, one further call without tools writes the reply.

## Showcase Run of All Usages

```bash
python scripts/run_showcase_examples.py
```

Runs the measured-decay inversion, five confirmed ideal-structure cases
(coupled/uncoupled, full and partial saturation) and a segmented CT slice
through the agent's tools without a language model. Outputs go to
`outputs/showcase/<time>/` (git-ignored) with `manifest.json` and a
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

For local runs you can put the key in an environment variable instead of
typing it in the page: `DEEPSEEK_API_KEY`, `OPENAI_API_KEY` or the generic
`LLM_API_KEY`. Streamlit secrets are not read. Never commit keys to the
repository.

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
Streamlit health check. Do not set API-key environment variables or secrets
on a public deployment; visitors enter their own key in the page.

## Inversion References

- Zou, Y.-L., Xie, R.-H., & Arad, A. (2016). Numerical estimation of choice of the
  regularization parameter for NMR T2 inversion. Petroleum Science, 13(2), 237–246.
  https://doi.org/10.1007/s12182-016-0093-6 (default smoothing-factor selection: the
  reciprocal of the absolute L-curve slope closest to 0.25 within 0.1–10).
- Hansen, P. C. (1992). Analysis of discrete ill-posed problems by means of the
  L-curve. SIAM Review, 34(4), 561–580. https://doi.org/10.1137/1034115
  (maximum-curvature option).
- Whittall, K. P., & MacKay, A. L. (1989). Quantitative interpretation of NMR
  relaxation data. Journal of Magnetic Resonance, 84(1), 134–152.
  https://doi.org/10.1016/0022-2364(89)90011-5 (non-negative least squares).

## Tests

```bash
python -m pytest
```

## Safety Boundary

The LLM only chooses among whitelisted Python tools and fills in their
arguments. It does not execute arbitrary code or shell commands from user
input, and all physical results come from the solvers.

## License

MIT License, see `LICENSE`. The `T2process` package keeps its own MIT license.
The literature notes in `docs/nmr_t2_literature_knowledge` summarize published
work in our own words and cite the original papers; they do not reproduce the
papers.
