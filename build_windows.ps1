param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ApiPath = Join-Path $RepoRoot "dvrs_tool\api.py"

function Get-ReleaseVersion {
    if (-not (Test-Path $ApiPath)) {
        throw "Unable to determine release version because '$ApiPath' was not found."
    }

    $apiContent = Get-Content -LiteralPath $ApiPath -Raw
    $match = [regex]::Match($apiContent, 'APP_VERSION\s*=\s*"(?<version>\d+\.\d+\.\d+)"')
    if (-not $match.Success) {
        throw "Unable to determine release version from dvrs_tool/api.py."
    }

    return $match.Groups["version"].Value
}

function Get-VersionSuffix {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Version
    )

    return ($Version -replace '\.', '')
}

function Remove-PathWithRetry {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LiteralPath,
        [int]$MaxAttempts = 5,
        [int]$DelayMilliseconds = 750
    )

    if (-not (Test-Path -LiteralPath $LiteralPath)) {
        return
    }

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            Remove-Item -LiteralPath $LiteralPath -Recurse -Force -ErrorAction Stop
            return
        }
        catch {
            if ($attempt -eq $MaxAttempts) {
                throw
            }
            Start-Sleep -Milliseconds $DelayMilliseconds
        }
    }
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host "==> $Description"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

$releaseVersion = Get-ReleaseVersion
$versionSuffix = Get-VersionSuffix -Version $releaseVersion
$buildOutputPath = ".\\build-release-$versionSuffix"
$distOutputPath = ".\\dist-release-$versionSuffix"

if ($Clean) {
    if (Test-Path ".\\build") {
        Remove-PathWithRetry -LiteralPath ".\\build"
    }
    if (Test-Path ".\\build-release") {
        Remove-PathWithRetry -LiteralPath ".\\build-release"
    }
    if (Test-Path ".\\dist") {
        Remove-PathWithRetry -LiteralPath ".\\dist"
    }
    if (Test-Path ".\\dist-release") {
        Remove-PathWithRetry -LiteralPath ".\\dist-release"
    }

    try {
        if (Test-Path -LiteralPath $buildOutputPath) {
            Remove-PathWithRetry -LiteralPath $buildOutputPath
        }
        if (Test-Path -LiteralPath $distOutputPath) {
            Remove-PathWithRetry -LiteralPath $distOutputPath
        }
    }
    catch {
        $versionedOutputExists = (Test-Path -LiteralPath $buildOutputPath) -or (Test-Path -LiteralPath $distOutputPath)
        if ($versionedOutputExists) {
            throw (
                "Clean failed for release version $releaseVersion because the existing versioned output folder is locked. " +
                "Close any process holding files in '$buildOutputPath' or '$distOutputPath', or supply a new version tag " +
                "in the code before rebuilding."
            )
        }
        throw
    }
}

Invoke-Step -Description "Install desktop build dependencies" -Command {
    python -m pip install -r requirements-desktop.txt
}

Invoke-Step -Description "Build Windows desktop package" -Command {
    python -m PyInstaller --noconfirm --clean --distpath $distOutputPath --workpath $buildOutputPath dvrs_desktop.spec
}
