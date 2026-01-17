<#
============================================================
tools/load_env_secret.ps1
------------------------------------------------------------
But :
  Charger les variables depuis .env.secret sans afficher les valeurs.
  Standard portfolio (APP1/APP2/APP3).

Usage :
  . .\tools\load_env_secret.ps1
  $env:ENABLE_AI="1"
  python -m vv_app2_tctc.main --out-dir data/outputs --verbose
============================================================
#>

$envFile = Join-Path $PSScriptRoot "..\.env.secret"

if (-not (Test-Path $envFile)) {
  Write-Error "Missing .env.secret at: $envFile"
  return
}

Get-Content $envFile | ForEach-Object {
  if ($_ -match "^\s*#") { return }
  if ($_ -match "^\s*$") { return }
  $name, $value = $_ -split "=", 2
  if ([string]::IsNullOrWhiteSpace($name)) { return }
  Set-Item -Path "Env:$name" -Value $value
}

Write-Host "OK: .env.secret loaded (values hidden)."
