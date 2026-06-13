$ErrorActionPreference = "Stop"

$envPath = Join-Path $PWD ".conda\emotion"

if (-not (Test-Path $envPath)) {
    throw "Conda 环境不存在，请先运行 scripts\create_conda_env.ps1"
}

$npmCmd = Join-Path $envPath "npm.cmd"
$originalPath = $env:PATH
$env:PATH = "$envPath;$env:PATH"

Push-Location frontend
try {
    & $npmCmd config set registry https://registry.npmmirror.com
    & $npmCmd ci
    & $npmCmd run build
}
finally {
    $env:PATH = $originalPath
    Pop-Location
}
