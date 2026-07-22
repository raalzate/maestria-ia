# Build the DDD Studio desktop bundle on Windows.
#
#   pwsh packaging/build.ps1
#
# Output: dist\DDD Studio\DDD Studio.exe  (onedir; wrap with Inno Setup later)
#
# Requires graphviz installed beforehand (provides dot.exe):
#   choco install graphviz
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "==> Installing desktop toolchain (pyinstaller, pywebview)"
uv sync --group desktop

Write-Host "==> Collecting the Graphviz dot.exe into packaging/graphviz/"
$GvDir = Join-Path $Root "packaging\graphviz"
if (Test-Path $GvDir) { Remove-Item -Recurse -Force $GvDir }
New-Item -ItemType Directory -Path $GvDir | Out-Null

$Dot = (Get-Command dot.exe -ErrorAction SilentlyContinue).Source
if (-not $Dot) {
    Write-Error "dot.exe not found on PATH. Install graphviz first: choco install graphviz"
    exit 1
}
# Copy dot.exe plus the graphviz bin dir DLLs/plugins it dlopens at runtime.
$DotDir = Split-Path $Dot -Parent
Copy-Item (Join-Path $DotDir "*") -Destination $GvDir -Recurse -Force

Write-Host "==> Running PyInstaller"
uv run pyinstaller packaging/ddd_studio.spec --noconfirm --clean

Write-Host "==> Done. Artifacts in dist/:"
Get-ChildItem dist
