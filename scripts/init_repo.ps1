if (-not (Test-Path ".git")) {
    git init
}

git status --short --branch

