$ErrorActionPreference = "Stop"

Write-Host "Generating course demo data in backend container..."
docker compose exec -T backend python -m app.scripts.seed_demo_data
Write-Host "Done. Use client@example.com / client123 and counselor@example.com / counselor123 to view demo history."
