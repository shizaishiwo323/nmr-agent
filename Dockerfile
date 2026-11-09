FROM condaforge/miniforge3:latest

WORKDIR /app
ENV PYTHONNOUSERSITE=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    STREAMLIT_SERVER_HEADLESS=true

COPY environment.docker.yml requirements.txt /app/
RUN mamba env create -f /app/environment.docker.yml && mamba clean -afy

COPY . /app

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD conda run --no-capture-output -n t2agent python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '8501') + '/_stcore/health', timeout=5).read()"

CMD ["bash", "-lc", "conda run --no-capture-output -n t2agent python -m streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port ${PORT:-8501} --server.headless true"]
