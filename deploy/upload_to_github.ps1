param(
    [string]$RepoUrl = "https://github.com/Lil-BobCN/NCHU_AI.git",
    [string]$Branch = "rag_java_dev",
    [string]$BaseBranch = "main",
    [string]$Proxy = "http://127.0.0.1:9910",
    [string]$CommitMessage = "Update rag_java internal RAG service"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$CloneDir = Join-Path $ProjectRoot ".upload_NCHU_AI_$Branch"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [string]$WorkingDirectory = $CloneDir
    )

    $gitArgs = @()
    if ($Proxy) {
        $gitArgs += @("-c", "http.proxy=$Proxy", "-c", "https.proxy=$Proxy")
    }
    $gitArgs += $Arguments

    Push-Location $WorkingDirectory
    try {
        & git @gitArgs
        if ($LASTEXITCODE -ne 0) {
            throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-GitOutput {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [string]$WorkingDirectory = $ProjectRoot
    )

    $gitArgs = @()
    if ($Proxy) {
        $gitArgs += @("-c", "http.proxy=$Proxy", "-c", "https.proxy=$Proxy")
    }
    $gitArgs += $Arguments

    Push-Location $WorkingDirectory
    try {
        $output = & git @gitArgs
        if ($LASTEXITCODE -ne 0) {
            throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
        }
        return $output
    }
    finally {
        Pop-Location
    }
}

function Remove-SensitiveFiles {
    param([string]$Root)

    Get-ChildItem -LiteralPath $Root -Recurse -Force -File |
        Where-Object {
            $_.Name -eq ".env" -or
            ($_.Name -like ".env.*" -and $_.Name -ne ".env.example") -or
            $_.Extension -eq ".pyc" -or
            $_.Name -like "*.tsbuildinfo"
        } |
        Remove-Item -Force
}

Write-Host "Project root: $ProjectRoot"
Write-Host "Target repo : $RepoUrl"
Write-Host "Target branch: $Branch"
Write-Host "Proxy: $Proxy"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is not installed or is not in PATH."
}

$remoteBranch = Invoke-GitOutput @("ls-remote", "--heads", $RepoUrl, $Branch)

if (-not (Test-Path -LiteralPath (Join-Path $CloneDir ".git"))) {
    if (Test-Path -LiteralPath $CloneDir) {
        throw "Upload working directory exists but is not a git repo: $CloneDir"
    }
    Invoke-Git @("clone", $RepoUrl, $CloneDir) -WorkingDirectory $ProjectRoot
}

Invoke-Git @("fetch", "origin")

if ($remoteBranch) {
    $localBranch = Invoke-GitOutput @("branch", "--list", $Branch) -WorkingDirectory $CloneDir
    if ($localBranch) {
        Invoke-Git @("switch", $Branch)
        Invoke-Git @("reset", "--hard", "origin/$Branch")
    }
    else {
        Invoke-Git @("switch", "-c", $Branch, "origin/$Branch")
    }
}
else {
    Invoke-Git @("switch", $BaseBranch)
    Invoke-Git @("reset", "--hard", "origin/$BaseBranch")
    $localBranch = Invoke-GitOutput @("branch", "--list", $Branch) -WorkingDirectory $CloneDir
    if ($localBranch) {
        Invoke-Git @("branch", "-D", $Branch)
    }
    Invoke-Git @("switch", "-c", $Branch)
}

$excludeDirs = @(
    ".git",
    ".venv",
    ".venv311",
    ".cache",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    ".vite",
    "uploads",
    "logs",
    ".upload_NCHU_AI_rag_java",
    ".upload_NCHU_AI_rag_java_dev",
    ".upload_preview",
    ".web_upload_rag_java",
    ".web_upload_rag_java_*"
)

$excludeFiles = @(
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.remote",
    "*.pyc",
    "*.pyo",
    "*.tsbuildinfo",
    "rag_java_deploy.tgz",
    "sample_contract.pdf",
    "acl.txt"
)

$robocopyArgs = @(
    $ProjectRoot,
    $CloneDir,
    "/MIR",
    "/XD"
) + $excludeDirs + @("/XF") + $excludeFiles

& robocopy @robocopyArgs
if ($LASTEXITCODE -gt 7) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

Remove-SensitiveFiles -Root $CloneDir

$badFiles = Get-ChildItem -LiteralPath $CloneDir -Recurse -Force -File |
    Where-Object {
        $_.Name -eq ".env" -or
        ($_.Name -like ".env.*" -and $_.Name -ne ".env.example") -or
        $_.Extension -eq ".pyc"
    }

if ($badFiles) {
    $badList = ($badFiles | Select-Object -ExpandProperty FullName) -join "`n"
    throw "Refusing to upload sensitive/generated files:`n$badList"
}

$status = Invoke-GitOutput @("status", "--porcelain") -WorkingDirectory $CloneDir
if (-not $status) {
    Write-Host "No changes to upload."
    exit 0
}

Invoke-Git @("add", "-A")
Invoke-Git @("commit", "-m", $CommitMessage)
Invoke-Git @("push", "-u", "origin", $Branch)

Write-Host "Uploaded successfully:"
Write-Host "  https://github.com/Lil-BobCN/NCHU_AI/tree/$Branch"
