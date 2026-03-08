# git-safe-merge.ps1
# Safe merge tool: pre-flight checks + merge current branch to main
# Aborts on any issue without modifying the repo.

param(
    [string]$TargetBranch = "main"
)

$ErrorActionPreference = "Stop"

function Write-Abort {
    param([string]$Message)
    Write-Host ""
    Write-Host "  ABORT: $Message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  OK    $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "  INFO  $Message" -ForegroundColor Cyan
}

$separator = "  " + ("-" * 40)

# -- 0. Verify we are inside a git repo -----------------------------------

$gitRoot = git rev-parse --show-toplevel 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Abort "not inside a git repository"
}

Write-Host ""
Write-Host "  git-safe-merge" -ForegroundColor Yellow
Write-Host $separator -ForegroundColor DarkGray
Write-Info "repo: $gitRoot"

# -- 1. Working tree must be clean ----------------------------------------

$status = git status --porcelain
if ($status) {
    Write-Abort "working tree not clean`n`n$status"
}
Write-Ok "working tree is clean"

# Check for merge in progress
if (Test-Path (Join-Path $gitRoot ".git/MERGE_HEAD")) {
    Write-Abort "a merge is currently in progress"
}

# Check for rebase in progress
$rebaseDirs = @(".git/rebase-merge", ".git/rebase-apply")
foreach ($d in $rebaseDirs) {
    if (Test-Path (Join-Path $gitRoot $d)) {
        Write-Abort "a rebase is currently in progress"
    }
}
Write-Ok "no merge or rebase in progress"

# -- 2. Detect current branch ---------------------------------------------

$currentBranch = git symbolic-ref --short HEAD 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Abort "detached HEAD state -- checkout a branch first"
}

if ($currentBranch -eq $TargetBranch) {
    Write-Abort "current branch is $TargetBranch -- switch to your working branch first"
}
Write-Ok "current branch: $currentBranch"

# -- 3. Fetch and verify sync with remote ---------------------------------

Write-Info "fetching from origin..."
git fetch origin 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Abort "git fetch failed -- check your network connection"
}

# Check current branch is not behind origin
$remoteBranch = "origin/$currentBranch"
$behindCurrent = git rev-list --count "$currentBranch..$remoteBranch" 2>&1
if ($LASTEXITCODE -eq 0 -and [int]$behindCurrent -gt 0) {
    Write-Abort "$currentBranch is $behindCurrent commit(s) behind $remoteBranch -- pull first"
}
Write-Ok "$currentBranch is up to date with $remoteBranch"

# Check main is not behind origin/main
$remoteTarget = "origin/$TargetBranch"
$localTargetExists = git rev-parse --verify $TargetBranch 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Abort "local branch '$TargetBranch' does not exist"
}

$behindMain = git rev-list --count "$TargetBranch..$remoteTarget" 2>&1
if ($LASTEXITCODE -eq 0 -and [int]$behindMain -gt 0) {
    Write-Abort "local $TargetBranch is $behindMain commit(s) behind $remoteTarget -- update $TargetBranch first"
}
Write-Ok "local $TargetBranch is up to date with $remoteTarget"

# -- 4. Simulate merge (dry run) ------------------------------------------

Write-Info "checking for conflicts..."

$mergeResult = git merge-tree --write-tree $TargetBranch $currentBranch 2>&1
$mergeExitCode = $LASTEXITCODE

if ($mergeExitCode -ne 0) {
    $conflictFiles = $mergeResult | Select-String "^CONFLICT" | ForEach-Object {
        if ($_ -match "CONFLICT.*:\s+(.+)$") { $Matches[1] }
        else { $_.ToString() }
    }

    $fileList = ""
    if ($conflictFiles) {
        $fileList = "`n`n  Conflicting files:`n"
        foreach ($f in $conflictFiles) {
            $fileList += "    - $f`n"
        }
    }
    Write-Abort "merge would create conflicts$fileList"
}
Write-Ok "no conflicts detected"

# Count commits that will be merged
$commitCount = git rev-list --count "$TargetBranch..$currentBranch"
$commitWord = if ([int]$commitCount -eq 1) { "commit" } else { "commits" }

# Show files that will change
$diffStat = git diff --stat "$TargetBranch...$currentBranch"

# -- 5. Summary ------------------------------------------------------------

Write-Host ""
Write-Host $separator -ForegroundColor DarkGray
Write-Host "  READY TO MERGE" -ForegroundColor Green
Write-Host ""
Write-Host "  Branch:    $currentBranch  ->  $TargetBranch" -ForegroundColor White
Write-Host "  Commits:   $commitCount $commitWord" -ForegroundColor White
Write-Host "  Conflicts: none" -ForegroundColor White
Write-Host ""
if ($diffStat) {
    Write-Host "  Changes:" -ForegroundColor White
    foreach ($line in $diffStat) {
        Write-Host "    $line" -ForegroundColor DarkGray
    }
    Write-Host ""
}

# -- 6. Confirmation -------------------------------------------------------

$answer = Read-Host "  Merge $currentBranch -> $TargetBranch ? (y/n)"
if ($answer -ne "y") {
    Write-Host ""
    Write-Host "  Cancelled." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

# -- 7. Execute merge ------------------------------------------------------

Write-Host ""
Write-Info "switching to $TargetBranch..."
git checkout $TargetBranch 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Abort "failed to checkout $TargetBranch"
}

Write-Info "merging $currentBranch..."
$mergeOutput = git merge $currentBranch 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  $mergeOutput" -ForegroundColor Red
    git checkout $currentBranch 2>&1 | Out-Null
    Write-Abort "merge failed -- switched back to $currentBranch"
}

Write-Info "pushing to origin/$TargetBranch..."
$pushOutput = git push origin $TargetBranch 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  $pushOutput" -ForegroundColor Red
    Write-Abort "push failed -- you are now on $TargetBranch with the merge applied locally"
}

Write-Info "switching back to $currentBranch..."
git checkout $currentBranch 2>&1 | Out-Null

Write-Host ""
Write-Host $separator -ForegroundColor DarkGray
Write-Host "  DONE" -ForegroundColor Green
Write-Host "  $currentBranch merged into $TargetBranch and pushed to origin" -ForegroundColor White
Write-Host ""
