# Public Deployment

This app includes a full pyGIMLi triangular-mesh 2D NMR simulation workflow.
The default no-upload path uses the repository-bundled ideal triangular-pore
input directly; uploaded red/yellow/white PNG phase maps are a separate input
route.
For that workflow, deploy from GitHub to a public host that supports Docker or
conda environments. Pure pip-only Streamlit Community Cloud builds may not
install pyGIMLi reliably.

The supported public image uses Python 3.11, installs the application science
stack from conda-forge, and installs `pygimli` from the PyPI wheel inside that
isolated conda environment. This combination was chosen after container
testing: the latest Linux `gimli::pygimli` conda package can solve the
environment, but its `pg.solve` runtime path crashed during the ideal-triangle
workflow in Docker.

## Local run

```bash
conda env create -f environment.docker.yml
conda activate t2agent
powershell -ExecutionPolicy Bypass -File scripts/run_streamlit_t2agent.ps1
```

## API keys

The public app ships without an API key. Each visitor opens **API settings**,
chooses a provider (DeepSeek, OpenAI or a custom OpenAI-compatible endpoint)
and enters their own key; the key is kept in the browser session only.

Do not configure API keys as secrets or environment variables on a public
deployment: the app reads `DEEPSEEK_API_KEY`, `OPENAI_API_KEY` and
`LLM_API_KEY` from the environment for local use, and on Streamlit Community
Cloud top-level secrets become environment variables, so a key stored there
would be spent by every visitor. Streamlit secrets are not read by the app.

## Entry point

Use this file as the Streamlit entry point:

```text
streamlit_app.py
```

## Recommended public Docker deployment

Use the repository `Dockerfile`. It creates the `t2agent` conda environment
from `environment.docker.yml` and starts:

```bash
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port ${PORT:-8501}
```

The Dockerfile also defines a Streamlit health check at `/_stcore/health`.

Recommended GitHub-backed hosts:

- Hugging Face Spaces with Docker SDK.
- Render Web Service from Dockerfile.
- Railway Dockerfile deployment.
- Any VPS or container host that builds the repository Dockerfile.

No Git submodule initialization is required. The ideal-triangle workflow used
by the public app is implemented inside this repository, so a fresh GitHub
checkout or Docker build has the same callable project files it needs.

After deployment, verify the public app by running an ideal-triangle request:

```text
Run the full 2D NMR simulation with the default ideal triangular pores and invert the T2 decay.
```

The result should include a pyGIMLi ideal-triangle mesh image/BMS, mesh quality
CSV/histogram, `Triangle_Raw_Decay.xlsx`, a standard decay workbook, and an
L-curve T2 spectrum. It should not require or generate a `rule_geometry_phase.png`
PNG input.

## Streamlit Community Cloud note

If you still create an app from Streamlit Community Cloud, use:

- Repository: `<owner>/nmr-agent`
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python version: Python 3.11 in Advanced settings

This mode is suitable only if pyGIMLi installs successfully on the Cloud build
image. The app's `requirements.txt` pins the verified `pygimli` and `pgcore`
wheel pair, but Community Cloud Python itself is selected in the deployment UI;
if the existing app was created with a different Python version, delete and
redeploy it with Python 3.11. For the required pyGIMLi mesh workflow,
Docker/conda deployment is still the preferred public path.

Leave **Advanced settings -> Secrets** empty (see *API keys* above).

## Notes

- Uploaded files and generated results are stored in the local `runs/` directory.
- On Streamlit Cloud this storage is temporary, so users should download the result zip.
- The agent uses function calling through an OpenAI-compatible API to choose whitelisted Python tools from `t2_agent.tools`; it does not execute arbitrary shell commands.
