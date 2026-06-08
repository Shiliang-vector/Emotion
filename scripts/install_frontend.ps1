$ErrorActionPreference = "Stop"

$envPath = Join-Path $PWD ".conda\emotion"

if (-not (Test-Path $envPath)) {
    throw "Conda 环境不存在，请先运行 scripts\create_conda_env.ps1"
}

$npmCmd = Join-Path $envPath "npm.cmd"
$nodeExe = Join-Path $envPath "node.exe"

Push-Location frontend
try {
    & $npmCmd config set registry https://registry.npmmirror.com
    & $npmCmd install
    & $nodeExe .\node_modules\vite\bin\vite.js build
}
finally {
    Pop-Location
}
