# training venv + system CUDA Toolkit (default v13.3)
# NO automatic download of pytorch.org CUDA wheels.
#
# Usage:
#   cd training
#   .\setup_cuda_env.ps1
#   .\setup_cuda_env.ps1 -TorchWheel 'D:\wheels\torch-xxx.whl'
#   . .\env_cuda.ps1
#   .\.venv\Scripts\Activate.ps1

param(
    [string]$CudaRoot = '',
    [string]$TorchWheel = '',
    [string]$TorchvisionWheel = '',
    [switch]$SkipVenv,
    [switch]$ForceRecreateVenv
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
Set-Location $Root

Write-Host '=== training: system CUDA only (no remote torch wheel) ===' -ForegroundColor Cyan

if (-not $CudaRoot) {
    if ($env:CUDA_PATH -and (Test-Path $env:CUDA_PATH)) {
        $CudaRoot = $env:CUDA_PATH
    } elseif (Test-Path 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3') {
        $CudaRoot = 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3'
    } else {
        $found = Get-ChildItem 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA' -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending | Select-Object -First 1
        if ($found) { $CudaRoot = $found.FullName }
    }
}
if (-not $CudaRoot -or -not (Test-Path $CudaRoot)) {
    Write-Error 'CUDA Toolkit not found. Install NVIDIA CUDA Toolkit first.'
}

$env:CUDA_PATH = $CudaRoot
$env:CUDA_HOME = $CudaRoot
$env:CUDA_ROOT = $CudaRoot
if ($CudaRoot -match 'v13\.3') { $env:CUDA_PATH_V13_3 = $CudaRoot }

$bin = Join-Path $CudaRoot 'bin'
$env:PATH = ($bin + ';' + (Join-Path $CudaRoot 'libnvvp') + ';' + $env:PATH)

Write-Host "CUDA_PATH = $CudaRoot"
$nvcc = Join-Path $bin 'nvcc.exe'
if (-not (Test-Path $nvcc)) { Write-Error "nvcc missing: $nvcc" }
& $nvcc --version | Select-Object -First 5

if ($SkipVenv) {
    Write-Host 'SkipVenv - done'
    exit 0
}

$py = $null
foreach ($cand in @('3.12', '3.11', '3.13')) {
    $out = & py "-$cand" -c 'import sys; print(sys.executable)' 2>$null
    if ($LASTEXITCODE -eq 0 -and $out) {
        $py = $out.Trim()
        Write-Host "Python: $py ($cand)"
        break
    }
}
if (-not $py) { Write-Error 'Need Python 3.11-3.13' }

$venvPath = Join-Path $Root '.venv'
if ((Test-Path $venvPath) -and $ForceRecreateVenv) {
    Write-Host 'Removing existing .venv ...'
    Remove-Item -Recurse -Force $venvPath
}
if (-not (Test-Path $venvPath)) {
    Write-Host 'Creating venv (no torch)...'
    & $py -m venv $venvPath
}

$python = Join-Path $venvPath 'Scripts\python.exe'
$pip = Join-Path $venvPath 'Scripts\pip.exe'
& $python -m pip install -U pip setuptools wheel

Write-Host 'Installing light deps from requirements-training.txt (no torch)...'
& $pip install -r (Join-Path $Root 'requirements-training.txt')

if ($TorchWheel) {
    if (-not (Test-Path $TorchWheel)) { Write-Error "TorchWheel not found: $TorchWheel" }
    Write-Host "Installing local torch wheel: $TorchWheel"
    & $pip install $TorchWheel
    if ($TorchvisionWheel) {
        if (-not (Test-Path $TorchvisionWheel)) { Write-Error "TorchvisionWheel not found: $TorchvisionWheel" }
        & $pip install $TorchvisionWheel
    }
    & $pip install 'ultralytics>=8.3.0'
} else {
    Write-Host ''
    Write-Host 'torch NOT installed (remote multi-GB wheel disabled).' -ForegroundColor Yellow
    Write-Host '  Local wheel later:'
    Write-Host "    .\setup_cuda_env.ps1 -TorchWheel 'D:\path\to\torch.whl'"
    Write-Host '  Or after activate:'
    Write-Host '    pip install path\to\torch.whl'
    Write-Host '    pip install ultralytics'
}

Write-Host ''
Write-Host '=== check ===' -ForegroundColor Cyan
Write-Host "CUDA_PATH=$env:CUDA_PATH"
& $nvcc --version | Select-Object -First 2
& $python -c 'print("python ok")'

Write-Host ''
Write-Host 'Done.' -ForegroundColor Green
Write-Host '  . .\env_cuda.ps1'
Write-Host '  .\.venv\Scripts\Activate.ps1'
