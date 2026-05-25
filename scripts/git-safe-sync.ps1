param(
    [switch]$Watch,
    [int]$IntervalSeconds = 60,
    [string]$Message = "",
    [switch]$SkipFetch,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step {
    param([string]$Text)
    Write-Host ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Text)
}

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [switch]$AllowFailure,
        [switch]$Quiet
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & git @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    if ($output -and -not $Quiet) {
        $output | ForEach-Object { Write-Host $_ }
    }
    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw "git $($Arguments -join ' ') failed with exit code $exitCode"
    }
    return @{ ExitCode = $exitCode; Output = $output }
}

function Get-RepoRoot {
    $rootResult = Invoke-Git -Arguments @("rev-parse", "--show-toplevel") -Quiet
    return ($rootResult.Output | Select-Object -First 1).Trim()
}

function Assert-NoBlockedStagedFiles {
    param([string[]]$StagedFiles)

    $blockedPatterns = @(
        '(^|/)\.env($|\.)',
        '(^|/)node_modules/',
        '(^|/)(\.venv|venv)/',
        '(^|/)\.pytest_cache/',
        '(^|/)\.ruff_cache/',
        '(^|/)__pycache__/',
        '\.(pem|key|p12|pfx|log|jsonl)$'
    )

    $allowed = @("backend/.env.example")
    $blocked = foreach ($path in $StagedFiles) {
        $normalized = $path -replace "\\", "/"
        if ($allowed -contains $normalized) {
            continue
        }
        foreach ($pattern in $blockedPatterns) {
            if ($normalized -match $pattern) {
                $normalized
                break
            }
        }
    }

    if ($blocked) {
        throw "Refusing to sync blocked files: $($blocked -join ', ')"
    }
}

function Assert-NoHighConfidenceSecrets {
    $secretPattern = 'sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----|xox[baprs]-[A-Za-z0-9-]{10,}'
    $scan = & git grep --cached -n -I -E $secretPattern -- . 2>$null
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        $scan | ForEach-Object { Write-Host $_ }
        throw "Refusing to sync because the staged snapshot contains high-confidence secret patterns."
    }
    if ($exitCode -ne 1) {
        throw "Secret scan failed with exit code $exitCode"
    }
}

function Invoke-OneSafeSync {
    $repoRoot = Get-RepoRoot
    Set-Location -LiteralPath $repoRoot

    $branch = (& git branch --show-current).Trim()
    if ($branch -ne "main") {
        $dirty = & git status --porcelain
        if ($dirty) {
            throw "Current branch is '$branch' with local changes. Switch or merge to main manually before auto-sync."
        }
        Write-Step "Switching from '$branch' to main"
        Invoke-Git -Arguments @("switch", "main") | Out-Null
    }

    if (-not $SkipFetch) {
        Write-Step "Fetching and fast-forwarding main"
        Invoke-Git -Arguments @("fetch", "origin") | Out-Null
        Invoke-Git -Arguments @("pull", "--ff-only", "origin", "main") | Out-Null
    }

    Write-Step "Staging trackable changes"
    Invoke-Git -Arguments @("add", "-A", "--", ".") | Out-Null

    $stagedFiles = & git diff --cached --name-only
    if (-not $stagedFiles) {
        Write-Step "No trackable changes to sync"
        return $false
    }

    Assert-NoBlockedStagedFiles -StagedFiles $stagedFiles
    Assert-NoHighConfidenceSecrets

    $whitespaceCheck = Invoke-Git -Arguments @("diff", "--cached", "--check") -AllowFailure
    if ($whitespaceCheck.ExitCode -ne 0) {
        Write-Warning "Whitespace warnings were found. They do not block sync, but should be cleaned during normal review."
    }

    if ($DryRun) {
        Write-Step "Dry run complete. Staged files:"
        $stagedFiles | ForEach-Object { Write-Host "  $_" }
        Invoke-Git -Arguments @("reset", "-q") | Out-Null
        return $true
    }

    $subject = if ([string]::IsNullOrWhiteSpace($Message)) {
        "Auto sync local project work to main"
    }
    else {
        $Message.Trim()
    }

    $commitArgs = @(
        "commit",
        "-m", $subject,
        "-m", "This checkpoint keeps GitHub main aligned with the current local project state while preserving the repository ignore boundary for secrets, caches, dependencies, and runtime logs.",
        "-m", "Constraint: Sync only Git-trackable files that pass the blocked-path and high-confidence secret checks.",
        "-m", "Rejected: Push ignored runtime files directly | would mix local machine state with durable project assets.",
        "-m", "Confidence: high",
        "-m", "Scope-risk: moderate",
        "-m", "Directive: Use scripts/git-safe-sync.ps1 or scripts/start-github-auto-sync.ps1 for future local-to-GitHub sync instead of ad hoc commits.",
        "-m", "Tested: branch guard; fast-forward pull; blocked-path filter; high-confidence staged secret scan.",
        "-m", "Not-tested: Full application build for every auto-sync interval.",
        "-m", "Co-authored-by: OmX <omx@oh-my-codex.dev>"
    )

    Write-Step "Committing staged snapshot"
    Invoke-Git -Arguments $commitArgs | Out-Null

    Write-Step "Pushing main to GitHub"
    Invoke-Git -Arguments @("push", "origin", "main") | Out-Null

    Write-Step "Sync complete"
    return $true
}

if ($Watch) {
    Write-Step "Starting GitHub auto-sync loop every $IntervalSeconds seconds"
    while ($true) {
        try {
            Invoke-OneSafeSync | Out-Null
        }
        catch {
            Write-Warning $_.Exception.Message
        }
        Start-Sleep -Seconds $IntervalSeconds
    }
}
else {
    Invoke-OneSafeSync | Out-Null
}
