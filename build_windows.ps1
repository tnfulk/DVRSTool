param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

if ($Clean) {
    if (Test-Path ".\\build") {
        Remove-Item -LiteralPath ".\\build" -Recurse -Force
    }
    if (Test-Path ".\\dist") {
        Remove-Item -LiteralPath ".\\dist" -Recurse -Force
    }
}

python -m pip install -r requirements-desktop.txt
python -m PyInstaller --noconfirm dvrs_desktop.spec
