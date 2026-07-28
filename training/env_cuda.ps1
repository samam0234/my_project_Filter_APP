# 시스템 설치 CUDA 13.3 을 현재 셸에 연결한다.
# (PyTorch 휠 다운로드 없음)
#
# 사용:
#   cd d:\my_project\CutNKeep\training
#   . .\env_cuda.ps1
#   .\.venv\Scripts\Activate.ps1   # venv 가 있을 때

$ErrorActionPreference = "Stop"

$CudaRoot = $env:CUDA_PATH
if (-not $CudaRoot -or -not (Test-Path $CudaRoot)) {
    $CudaRoot = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3"
}
if (-not (Test-Path $CudaRoot)) {
    Write-Error "CUDA Toolkit 을 찾을 수 없습니다. 예상 경로: $CudaRoot"
}

$env:CUDA_PATH = $CudaRoot
$env:CUDA_PATH_V13_3 = $CudaRoot
$env:CUDA_HOME = $CudaRoot
$env:CUDA_ROOT = $CudaRoot

# PATH: CUDA bin / libnvvp 우선
$bin = Join-Path $CudaRoot "bin"
$libnvvp = Join-Path $CudaRoot "libnvvp"
$parts = @($bin, $libnvvp) + @($env:PATH -split ';' | Where-Object { $_ -and $_ -notmatch 'CUDA\\v' })
$env:PATH = ($parts -join ';')

# 일부 빌드 도구가 참조
$env:INCLUDE = "$(Join-Path $CudaRoot 'include');$env:INCLUDE"
$env:LIB = "$(Join-Path $CudaRoot 'lib\x64');$env:LIB"

Write-Host "[env_cuda] CUDA_PATH=$env:CUDA_PATH" -ForegroundColor Green
$nvcc = Join-Path $bin "nvcc.exe"
if (Test-Path $nvcc) {
    & $nvcc --version | Select-Object -First 5
} else {
    Write-Warning "nvcc 없음: $nvcc"
}

# training venv 가 있으면 안내만 (자동 활성화는 선택)
$venvAct = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvAct) {
    Write-Host "[env_cuda] venv 활성화: .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
} else {
    Write-Host "[env_cuda] training\.venv 없음 — setup_cuda_env.ps1 로 생성 가능 (torch 자동 다운로드 안 함)" -ForegroundColor Yellow
}
