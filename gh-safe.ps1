param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ghCandidates = @(
    "C:\Program Files\GitHub CLI\gh.exe",
    "$env:LOCALAPPDATA\Programs\GitHub CLI\gh.exe"
)

$ghPath = $ghCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $ghPath) {
    throw "GitHub CLI was not found. Install it first with winget install --id GitHub.cli -e --source winget."
}

$proxyVars = @(
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy"
)

$savedValues = @{}

foreach ($name in $proxyVars) {
    $savedValues[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
    [Environment]::SetEnvironmentVariable($name, $null, "Process")
}

try {
    & $ghPath @Args
    exit $LASTEXITCODE
}
finally {
    foreach ($name in $proxyVars) {
        [Environment]::SetEnvironmentVariable($name, $savedValues[$name], "Process")
    }
}
