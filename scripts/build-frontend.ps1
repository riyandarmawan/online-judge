# Build Vue production bundle and copy it to OJ_Backend/dist
# so Docker/nginx can serve the app without `npm run dev`.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Frontend = Join-Path $Root "OJ_Frontend"
$Dest = Join-Path $Root "OJ_Backend\dist"

Set-Location $Frontend
if (-not (Test-Path "node_modules")) {
  npm install
}
if (-not (Get-ChildItem "static\js\vendor.dll*.js" -ErrorAction SilentlyContinue)) {
  $env:NODE_ENV = "development"
  npm run build:dll
}
$env:NODE_ENV = "production"
npm run build

if (-not (Test-Path "dist\index.html")) {
  throw "Build gagal: OJ_Frontend/dist/index.html tidak ditemukan."
}

if (Test-Path $Dest) {
  Remove-Item -Recurse -Force $Dest
}
Copy-Item -Recurse "dist" $Dest
Write-Host "Frontend production disalin ke $Dest"
Write-Host "Restart backend agar nginx memuat file baru:"
Write-Host "  cd Deploy; docker compose restart oj-backend"
