param(
    [int]$Port = 8501,
    [string]$Address = "localhost",
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")

$candidates = @()
if ($Python) {
    $candidates += $Python
}
if ($env:T2AGENT_PYTHON) {
    $candidates += $env:T2AGENT_PYTHON
}
$candidates += Join-Path $env:USERPROFILE ".conda\envs\t2agent\python.exe"

$PythonExe = $null
foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path -LiteralPath $candidate)) {
        $PythonExe = (Resolve-Path -LiteralPath $candidate).Path
        break
    }
}

if (-not $PythonExe) {
    Write-Error "Cannot find the t2agent Python executable. Create it with: conda env create -f environment.docker.yml"
    exit 1
}

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue
    Write-Error "Port $Port is already in use by PID $($listener.OwningProcess): $($proc.CommandLine). Stop that explicit process first, then rerun this script."
    exit 1
}

$env:PYTHONNOUSERSITE = "1"
Set-Location $Root

& $PythonExe "scripts/check_t2agent_env.py"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& $PythonExe -m streamlit run "streamlit_app.py" --server.address $Address --server.port $Port --server.headless true
