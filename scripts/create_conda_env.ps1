$ErrorActionPreference = "Stop"

$envPath = Join-Path $PWD ".conda\emotion"

if (-not (Test-Path $envPath)) {
    conda env create --prefix $envPath --file environment.yml
} else {
    conda env update --prefix $envPath --file environment.yml --prune
}

conda run --prefix $envPath python --version

$pythonExe = Join-Path $envPath "python.exe"
$npmCmd = Join-Path $envPath "npm.cmd"

& $npmCmd config set registry https://registry.npmmirror.com
& $pythonExe -m pytest
