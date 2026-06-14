$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-True($Condition, $Message) {
    if (-not $Condition) {
        throw $Message
    }
    Write-Host "OK  $Message" -ForegroundColor Green
}

Write-Step "Checking Docker Compose services"
$services = docker compose ps --format json | ForEach-Object { $_ | ConvertFrom-Json }
$required = @("postgres", "backend", "frontend", "deepface", "sensevoice")
foreach ($name in $required) {
    $service = $services | Where-Object { $_.Service -eq $name } | Select-Object -First 1
    Assert-True $service "service '$name' exists"
    Assert-True ($service.State -eq "running") "service '$name' is running"
}

Write-Step "Checking backend health"
$health = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get
Assert-True ($health.status -eq "ok") "backend health endpoint returns ok"

Write-Step "Checking frontend"
$frontend = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing
Assert-True ($frontend.StatusCode -eq 200) "frontend returns HTTP 200"

Write-Step "Checking demo account login"
$loginBody = @{
    username = "client@example.com"
    password = "client123"
}
$login = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/jwt/login" -Method Post -Body $loginBody -ContentType "application/x-www-form-urlencoded"
Assert-True $login.access_token "client demo account can login"

$headers = @{ Authorization = "Bearer $($login.access_token)" }
$me = Invoke-RestMethod -Uri "http://localhost:8000/api/users/me" -Method Get -Headers $headers
Assert-True ($me.email -eq "client@example.com") "client demo account /api/users/me works"

$tasks = Invoke-RestMethod -Uri "http://localhost:8000/api/me/tasks" -Method Get -Headers $headers
Write-Host "Demo client task count: $($tasks.Count)"

Write-Host ""
Write-Host "Demo check passed." -ForegroundColor Green
