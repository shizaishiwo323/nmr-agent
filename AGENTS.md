# NMR Simulation and T2 Inversion Agent

## Project Purpose

This project builds a guided AI agent for a complete NMR simulation and T2
analysis workflow. The agent should help users move from geometry input to
mesh generation, NMR/M2 simulation solving, simulated time-domain decay
generation, T2 inversion, visualization, optional peak decomposition, and
result interpretation.

The agent must also support narrower workflows. A user may ask to run the full
simulation pipeline for testing, or may only need T2 inversion, visualization,
or Gaussian decomposition using existing decay or spectrum data.

The intended experience is conversational and guided. The agent should not
expect new users to already understand terms such as regularization factor,
L-curve, T2 spectrum, Gaussian peak decomposition, mesh quality, binary image
geometry, or pore/solid phase labels. It should explain each choice in
practical scientific language, ask only the questions needed to finish the
task, and call the local processing code to produce files and figures.

The project scope is focused on NMR simulation and T2 processing. Ideas from
`AI_for_Geophysics智能体会议纪要_整理版.md` provide the broader agent-workflow
philosophy, but new work should stay centered on the NMR geometry -> mesh ->
simulation -> T2 inversion pipeline and the existing T2 capabilities in
`T2process`.

## Core User Workflow

The agent should guide the user through these stages:

1. Understand the user's goal.
   - Full NMR simulation workflow: geometry input, meshing, NMR/M2 solving,
     decay generation, T2 inversion, visualization, and interpretation.
   - Full simulation workflow as a test run with default settings.
   - T2 inversion only.
   - T2 inversion plus visualization.
   - T2 inversion plus Gaussian peak decomposition.
   - Visualization of existing inversion results.
   - Gaussian decomposition of an existing T2 spectrum.

2. Choose and validate the input route.
   - Parametric geometry input: let the user configure regular geometry
     rules, whether multiple geometry elements are coupled/combined, and their
     dimensions.
   - Image geometry input: accept a two-dimensional binary image, preferably a
     PNG using the project's default color convention, such as red for liquid
     pore phase and yellow for solid phase.
   - Existing decay-data input: accept Excel workbooks for T2 inversion-only
     workflows.
   - Existing spectrum input: accept spectrum workbooks for visualization or
     Gaussian decomposition-only workflows.

3. Inspect uploaded decay data when T2 inversion is requested.
   - Accept Excel workbooks as the primary input format.
   - Expect the first column to contain time values.
   - Expect one or more following columns to contain decay signal amplitudes.
   - Detect valid numeric rows even when time cells contain strings such as
     scientific notation or simple text with units.
   - Tell the user clearly if the table is empty, has no valid time column,
     has no valid signal column, or has too few valid data points.
   - When safe and unambiguous, normalize the data format internally instead
     of forcing the user to edit the table manually.

4. Ask for required scientific and processing choices.
   - For geometry input: geometry type/rules, dimensions, coupling/combination
     options, phase labels, and any known physical scale.
   - For image input: confirm the binary color convention and whether white
     borders or margins should be auto-cropped.
   - For meshing: use the PyGIMLi-based meshing method by default. Do not add
     alternative mesh engines unless the project explicitly adopts and tests
     them.
   - For NMR/M2 simulation: ask only for required solver parameters that are
     not safely covered by defaults.
   - Whether the time column is already in milliseconds or needs conversion
     from seconds to milliseconds.
   - Whether the signal should be trimmed from the global peak before
     inversion.
   - Whether to use fixed regularization or L-curve automatic selection.
   - T2 range and number of T2 bins, if the user needs non-default settings.
   - Number of Gaussian peaks, if peak decomposition is requested.
   - Output location and preferred result artifacts.

5. Run the local processing code.
   - Use the standardized NMR simulation package or integration wrapper once
     it is added to this project.
   - Use the standardized Python package under `T2process/nmr_t2`.
   - Do not reimplement inversion, L-curve, plotting, or Gaussian fitting
     logic in the web layer when the package already provides it.
   - Do not reimplement geometry parsing, meshing, or simulation solver logic
     in the web layer when an integrated local package already provides it.

6. Display process data progressively.
   - Show geometry validation results as soon as they are available.
   - Show cropped/normalized binary images before meshing.
   - Show generated meshes immediately after meshing completes.
   - Show simulation fields, intermediate solver outputs, and generated
     time-domain curves as soon as each step completes.
   - Show T2 spectra, fits, L-curve diagnostics, and Gaussian decomposition
     outputs as soon as they are produced.
   - Do not wait until the entire pipeline is finished before updating the
     result panel.

7. Explain results.
   - Summarize generated files.
   - Explain geometry, mesh, simulation, and decay-generation outputs in
     practical terms.
   - Explain selected regularization values and whether L-curve selection was
     used.
   - Explain T2 peak positions, areas, and area fractions when Gaussian
     decomposition is performed.
   - Warn when image quality, mesh quality, solver convergence, data quality,
     point count, noise, or chosen peak count may make the interpretation
     unreliable.

## Full NMR Simulation Workflow

The full workflow should be treated as a staged scientific pipeline:

1. Geometry input or upload.
2. Geometry validation and normalization.
3. Mesh generation using the PyGIMLi-based method.
4. NMR/M2 simulation solving.
5. Time-domain decay curve generation.
6. T2 inversion using the mature local T2 pipeline.
7. Visualization and optional Gaussian peak decomposition.
8. Interpretation and artifact summary.

Each stage should produce user-visible process data and downloadable artifacts
where appropriate. If a later stage fails, the agent should still preserve and
show the successful earlier-stage artifacts.

The GitHub repository provided by the user for the simulation code should be
treated as the intended integration source, but its exact callable interfaces
must be inspected before implementation. Do not invent solver function names or
file formats that have not been verified in the integrated code.

## Geometry Input and Meshing

The app should support two geometry input modes.

### Rule-Based Geometry Input

The user should be able to configure regular geometry shapes and dimensions in
the web UI. The agent should guide the user through:

- Geometry type or rule.
- Whether geometry elements are independent or coupled/combined.
- Dimensions and scale.
- Phase assignment for pore/liquid and solid regions.
- Mesh-generation defaults.

The default meshing method is the PyGIMLi-based method used by the simulation
workflow. The app should expose only the necessary mesh parameters at first and
keep advanced settings hidden unless the user asks for them or a validation
problem requires them.

### Image-Based Geometry Input

The user may upload a two-dimensional binary image, preferably PNG. The agent
should tell users clearly that the image must contain only two material phases.
The default project convention is:

- Red: liquid or pore phase.
- Yellow: solid phase.

If the uploaded image has a white border or white margin, the app should detect
and crop that border automatically when it is safe to do so. The cropped image
should be shown to the user before meshing. If the image contains unexpected
extra colors or ambiguous antialiasing, the agent should explain the problem
and either offer a safe thresholding/repair step or ask the user for a cleaner
binary image.

The original uploaded image must be preserved. Cropped, thresholded, or
normalized images must be written as derived artifacts with provenance.

## Local T2 Processing Capabilities

The available processing code is in `T2process/nmr_t2`.

### Fixed-Regularization NNLS Inversion

Main callable workflow:

- `nmr_t2.pipelines.run_nnls_workbook`

Purpose:

- Converts decay data into a T2 spectrum using NNLS inversion with a user-set
  regularization factor.

Important parameters:

- `regularization`: smoothing/regularization weight. Larger values generally
  make the T2 spectrum smoother but may merge real peaks. Smaller values can
  preserve sharper structure but may amplify noise.
- `t2_min_ms` and `t2_max_ms`: lower and upper T2 search bounds in ms.
- `num_bins`: number of logarithmic T2 bins.
- `trim_from_peak`: whether to start inversion from the global maximum.
- `time_to_ms_scale`: multiplier used to convert input time to milliseconds.

Default configuration:

- `num_bins = 200`
- `regularization = 1.0`
- `t2_min_ms = 1.0`
- `t2_max_ms = 10000.0`
- `min_points_after_trim = 10`

Generated artifacts:

- `*_nnls_spectrum.xlsx`
- `*_nnls_trimmed_decay.xlsx`
- `*_nnls_fit.xlsx`
- `*_nnls_summary.csv`
- `*_nnls_summary.xlsx`

The fit workbook keeps the inversion-sampled decay, fitted amplitude, and
signed residual noise in adjacent columns. The legacy `residual` column is
retained as an alias of `noise_amplitude`.

### L-Curve Regularization Selection

Main callable workflow:

- `nmr_t2.pipelines.run_lcurve_workbook`

Purpose:

- Tests a range of regularization values and selects a preferred value using
  the L-curve reciprocal-slope criterion.

Use this mode when:

- The user does not know how to choose a regularization factor.
- The user wants a more defensible automatic choice.
- The user is doing exploratory inversion and wants diagnostic plots.

Explain to users:

- The regularization factor balances data fitting against smoothness.
- Very weak regularization may fit noise.
- Very strong regularization may hide real pore-size or relaxation components.
- L-curve selection searches for a compromise between these two effects.

Default configuration:

- `num_bins = 200`
- `t2_min_ms = 0.01`
- `t2_max_ms = 100000.0`
- `alpha_min = 1e-6`
- `alpha_max = 1e2`
- `alpha_count = 60`
- `slope_reciprocal_target = 0.25`
- `slope_reciprocal_valid_range = (0.1, 10.0)`
- `min_points_after_trim = 10`

Generated artifacts:

- `*_lcurve_spectrum.xlsx`
- `*_lcurve_metrics.xlsx`
- `*_lcurve_trimmed_decay.xlsx`
- `*_lcurve_fit.xlsx`
- `*_lcurve_summary.csv`
- `*_lcurve_summary.xlsx`
- L-curve diagnostic figures.

### Decay and T2 Spectrum Visualization

Main callable workflow:

- `nmr_t2.pipelines.run_plotting_workbook_pair`

Purpose:

- Generates paired figures showing raw decay data and the corresponding T2
  spectrum.

Input requirements:

- A raw decay workbook.
- A spectrum workbook produced by NNLS or L-curve inversion.

Generated artifacts:

- `*_decay_t2.png`

### Gaussian Peak Decomposition

Main callable workflow:

- `nmr_t2.pipelines.run_gaussian_decomposition_on_spectrum_workbook`

Purpose:

- Fits the T2 spectrum as a sum of Gaussian components in log10(T2) space.

Important parameters:

- `peak_count`: number of peaks/components to fit.
- `max_function_evals`: maximum fitting function evaluations.
- `max_iterations`: fallback optimizer iteration limit.

Default configuration:

- `peak_count = 3`
- `max_function_evals = 20000`
- `max_iterations = 2000`

Explain to users:

- Peak decomposition is an interpretation aid, not a guarantee that the sample
  truly has exactly that many physical pore populations.
- More peaks can fit complex spectra but may overfit noise.
- Fewer peaks are easier to interpret but may merge distinct relaxation
  components.
- If the user has no prior knowledge, suggest starting with 2 or 3 peaks and
  comparing fit quality and interpretability.

Generated artifacts:

- `*_gaussian_peak_table.xlsx`
- `*_gaussian_fit.xlsx`
- `*_gaussian_summary.csv`
- `*_gaussian_summary.xlsx`
- Gaussian decomposition figures.

## Agent Guidance Principles

The agent should behave like a scientific workflow assistant.

- First clarify the user's scientific goal, not just the button they want to
  press.
- Detect whether the user wants a full simulation workflow or only an existing
  T2 inversion/visualization/decomposition workflow.
- For full simulation, guide the user step by step through geometry, meshing,
  solving, decay generation, inversion, and interpretation instead of asking
  for every parameter at once.
- Use defaults when the user is unsure, but state what the default means.
- Prefer L-curve regularization for beginner users unless they explicitly know
  the fixed regularization value they want.
- Ask for fixed regularization only when the user has prior runs, a reference
  method, or a reason to reproduce a specific setting.
- Ask about time units early because wrong time scaling changes the physical
  meaning of T2.
- Ask about trimming from the global peak, especially for simulated data with
  an initial rise before decay.
- For image-based geometry, explain that the uploaded image must be binary and
  phase-coded. Warn users when antialiasing, compression artifacts, or extra
  colors make the geometry ambiguous.
- For mesh and simulation stages, explain failures in practical terms: invalid
  geometry, too-small features for the mesh, disconnected regions, poor mesh
  quality, or solver convergence issues.
- Do not overwhelm the user with all parameters at once.
- Update the right-side result panel after each completed stage.
- After each run, give a short interpretation and list generated files.
- When results are uncertain, say why instead of presenting them as final
  scientific truth.

## Suggested Beginner Defaults

When the user is unsure:

- For a complete pipeline test, use a simple rule-based geometry with default
  dimensions, PyGIMLi meshing, default simulation settings, L-curve inversion,
  and paired decay/T2 visualization.
- For image geometry, assume red is liquid/pore phase and yellow is solid phase
  unless the user says otherwise.
- Auto-crop white image borders when the crop is unambiguous, but preserve the
  original image.
- Use L-curve inversion.
- Use `time_to_ms_scale = 1.0` if time is already in ms.
- Use `time_to_ms_scale = 1000.0` if time is in seconds.
- Use `trim_from_peak = true` for simulation-style data that rises before
  decaying.
- Use `trim_from_peak = false` for clean experimental decay data that starts
  at the maximum.
- Use default T2 bounds unless the user knows the expected relaxation range.
- For Gaussian decomposition, start with `peak_count = 2` or `3` depending on
  the visible spectrum complexity.

## Web Application Expectations

The web app should provide:

- File upload for Excel decay/spectrum data.
- File upload for binary PNG geometry images.
- Rule-based geometry controls for regular geometry, coupled/combined geometry
  options, and geometry dimensions.
- Data, image, and geometry preview with validation feedback.
- Model selection UI for the language agent.
- A guided parameter panel driven by the agent conversation.
- Controls for geometry setup, PyGIMLi-based meshing, NMR/M2 simulation solving,
  and simulated decay generation.
- Controls for fixed NNLS, L-curve inversion, plotting, and Gaussian
  decomposition.
- A right-side result panel that updates progressively as each stage completes.
- Intermediate process previews, including normalized/cropped image, generated
  mesh, simulation outputs, time-domain curve, T2 spectrum, fit diagnostics,
  and Gaussian peak tables/figures.
- Output file download links.
- Figure previews.
- Clear warnings when input format or parameters are unsuitable.
- Clear status messages for queued, running, completed, warning, and failed
  stages.

DeepSeek API credentials must be read from environment variables, not hardcoded
in source files or documentation.

Recommended environment variable:

- `DEEPSEEK_API_KEY`

The API base URL can be configured separately:

- `DEEPSEEK_BASE_URL=https://api.deepseek.com`

## Model Selection Expectations

The web app should let users choose among available DeepSeek-compatible modes
or aliases configured by the project, such as:

- A fast chat mode for ordinary guidance.
- A stronger reasoning mode for complex parameter decisions.
- A non-reasoning mode when the user wants faster, simpler interaction.

Model display names in the UI may be user-friendly, but backend code should map
them to explicit provider model IDs in one place.

## Data and File Safety

- Do not store API keys in the repository.
- Do not silently overwrite important user outputs unless the output directory
  is clearly run-specific or the user confirms replacement.
- Preserve raw uploaded data.
- Preserve raw uploaded geometry images.
- Write normalized or repaired data as a new derived artifact.
- Write cropped, thresholded, meshed, simulated, inverted, plotted, and
  decomposed outputs as stage-specific artifacts.
- Keep enough provenance in summaries to reproduce the run.
- Use run-specific output directories for full simulation pipelines whenever
  possible.
- Do not treat intermediate process data as disposable. It is part of the
  scientific audit trail and should remain available to the user.

## Repository Operating Rules

The following rules apply to all agents working in this repository:

- Do not batch-delete files or directories.
- Do not use `del /s`, `rd /s`, `rmdir /s`, `Remove-Item -Recurse`, or
  `rm -rf`.
- If a file must be deleted, delete only one explicit file path at a time.
- If many files need deletion, stop and ask the user to delete them manually.
- For generic repository inspection or one-off scripts, conda `base` may be
  used only when no project dependencies are needed.
- For this project app, tests, PyGIMLi meshing, NMR simulation, Streamlit
  debugging, or any command that imports project packages, use the verified
  conda environment:
  `C:\Users\imgw\.conda\envs\t2agent\python.exe`.
- Before starting Streamlit or diagnosing pyGIMLi errors, run:
  `set PYTHONNOUSERSITE=1` and
  `C:\Users\imgw\.conda\envs\t2agent\python.exe scripts\check_t2agent_env.py`.
- Start the local app with:
  `powershell -ExecutionPolicy Bypass -File scripts/run_streamlit_t2agent.ps1`.
  Do not start it with `python -m streamlit run streamlit_app.py` from conda
  `base`, global Python, or an unverified terminal.
- If port `8501` is already occupied, inspect the owning process first. It must
  be `C:\Users\imgw\.conda\envs\t2agent\python.exe`; otherwise stop only that
  explicit PID and restart with `scripts/run_streamlit_t2agent.ps1`.
- Do not work around `pyGIMLi meshtools are not available` by adding fallback
  mesh engines or bypassing the simulation stage. Treat it as an environment
  failure until `scripts/check_t2agent_env.py` passes in `t2agent`.
- For public Streamlit deployment, keep the runtime on Python 3.11 and verify
  that `requirements.txt` / deployment settings install `pygimli` successfully
  before testing the ideal triangular pore workflow.

