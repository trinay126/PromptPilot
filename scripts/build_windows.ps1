$ErrorActionPreference = "Stop"
$Version = if ($env:RELEASE_VERSION) { $env:RELEASE_VERSION } else { "dev" }
$OutputDir = "artifacts\promptpilot-$Version-windows-x64"

Write-Host "Cleaning previous artifacts..."
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist, artifacts
Remove-Item -Force -ErrorAction SilentlyContinue promptpilot.spec
New-Item -ItemType Directory -Force $OutputDir | Out-Null

Write-Host "Installing build dependencies..."
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

Write-Host "Running tests..."
python -m pytest

Write-Host "Building promptpilot.exe..."
python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --console `
    --name promptpilot `
    --paths src `
    src\promptpilot\__main__.py

Copy-Item dist\promptpilot.exe "$OutputDir\promptpilot.exe"
@{
    product = "PromptPilot"
    version = $Version
    platform = "windows-x64"
    python = (python --version)
    built_utc = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json | Set-Content "$OutputDir\release-manifest.json"

Get-FileHash "$OutputDir\promptpilot.exe" -Algorithm SHA256 |
    ForEach-Object { "$($_.Hash)  $($_.Path | Split-Path -Leaf)" } |
    Set-Content "$OutputDir\SHA256SUMS.txt"

Compress-Archive -Path "$OutputDir\*" -DestinationPath "artifacts\promptpilot-$Version-windows-x64.zip"
Write-Host "Release bundle: artifacts\promptpilot-$Version-windows-x64.zip"
