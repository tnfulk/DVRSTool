param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

if ($Clean) {
    if (Test-Path ".\\build") {
        Remove-Item -LiteralPath ".\\build" -Recurse -Force
    }
    if (Test-Path ".\\build-release") {
        Remove-Item -LiteralPath ".\\build-release" -Recurse -Force
    }
    if (Test-Path ".\\dist") {
        Remove-Item -LiteralPath ".\\dist" -Recurse -Force
    }
    if (Test-Path ".\\dist-release") {
        Remove-Item -LiteralPath ".\\dist-release" -Recurse -Force
    }
}

python -m pip install -r requirements-desktop.txt
python -m PyInstaller --noconfirm --clean --distpath .\\dist-release --workpath .\\build-release dvrs_desktop.spec
