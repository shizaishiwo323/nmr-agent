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

## Secrets

Set the DeepSeek key in Streamlit Cloud secrets:

```toml
DEEPSEEK_API_KEY = "your-new-key"
```

Do not commit `.streamlit/secrets.toml`.

The web page also includes a password input for users to provide their own
DeepSeek API key at runtime. Runtime input takes priority over Streamlit
Secrets and is not written to disk by the app.

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
用默认理想三角孔跑完整二维 NMR 模拟，并做 T2 反演
```

The result should include a pyGIMLi ideal-triangle mesh image/BMS, mesh quality
CSV/histogram, `Triangle_Raw_Decay.xlsx`, a standard decay workbook, and an
L-curve T2 spectrum. It should not require or generate a `rule_geometry_phase.png`
PNG input.

## Streamlit Community Cloud note

If you still create an app from Streamlit Community Cloud, use:

- Repository: `shizaishiwo323/nmr-agent`
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python version: Python 3.11 in Advanced settings

This mode is suitable only if pyGIMLi installs successfully on the Cloud build
image. The app's `requirements.txt` pins the verified `pygimli` and `pgcore`
wheel pair, but Community Cloud Python itself is selected in the deployment UI;
if the existing app was created with a different Python version, delete and
redeploy it with Python 3.11. For the required pyGIMLi mesh workflow,
Docker/conda deployment is still the preferred public path.

If you want the public app to have a default DeepSeek key, add it through
Streamlit Cloud **Advanced settings -> Secrets**. If you leave secrets empty,
the app still works, but each user must enter their own DeepSeek API key in the
web page.

## Notes

- Uploaded files and generated results are stored in the local `runs/` directory.
- On Streamlit Cloud this storage is temporary, so users should download the result zip.
- The agent uses DeepSeek function calling to choose whitelisted Python tools from `t2_agent.tools`; it does not execute arbitrary shell commands.
