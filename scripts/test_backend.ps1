$ErrorActionPreference = "Stop"

$envPath = Join-Path $PWD ".conda\emotion"

if (-not (Test-Path $envPath)) {
    throw "Conda 环境不存在，请先运行 scripts\create_conda_env.ps1"
}

$pythonExe = Join-Path $envPath "python.exe"
& $pythonExe -m pytest
