<#
.SYNOPSIS
  Jingyu (Static-Yu) - one-shot "reset + push to GitHub" script.
.DESCRIPTION
  Local .git is broken (corrupt loose object) and the AI sandbox refuses
  to touch .git/ paths, so we reset cleanly and push.
  This script will:
    1) Delete broken .git
    2) git init + initial commit
    3) gh repo create jingyu (public) + push
    4) Set repo description and topics
.NOTES
  Requires:
    - git  (D:\GIT\CMD\git.exe already in PATH)
    - gh   (D:\githubcil\gh.exe already in PATH - non-standard)
    - gh auth login (sunday-lil, repo scope confirmed)
#>

# --- Force UTF-8 for this script's output (defensive) ---
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ErrorActionPreference = "Stop"
$ProjectDir = "c:\Users\Administrator\Desktop\webwrold"
$GhExe      = "D:\githubcil\gh.exe"
$RepoName   = "jingyu"
$RepoDesc   = "Jingyu (Jing-Yu) - an end-to-end encrypted healing web app: guqin 5-yin music, encrypted diary bottles, mood checkin, spirit garden, and a secret admin backend. Non-commercial. Privacy-first. Light-touch."
# Topics: AVOID DASHES (PowerShell parser interprets -xxx as a parameter)
$Topics     = @("fastapi","jinja2","healing","mental-health","privacy","sqlite","python","jinja","healing-app","diary","end_to_end_encryption")

Set-Location $ProjectDir

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Jingyu -> GitHub one-shot reset+push" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/6] Removing broken .git ..." -ForegroundColor Yellow
if (Test-Path .git) {
    Remove-Item .git -Recurse -Force
    Write-Host "      OK" -ForegroundColor Green
} else {
    Write-Host "      No .git found, skip" -ForegroundColor DarkYellow
}

Write-Host "[2/6] git init -b main ..." -ForegroundColor Yellow
git init -b main | Out-Null
Write-Host "      OK" -ForegroundColor Green

Write-Host "[3/6] git add -A ..." -ForegroundColor Yellow
git add -A
$fileCount = (git ls-files | Measure-Object).Count
Write-Host ("      OK  ({0} files staged)" -f $fileCount) -ForegroundColor Green

Write-Host "[4/6] git commit ..." -ForegroundColor Yellow
git -c user.name="sunday-lil" `
    -c user.email="sunday-lil@users.noreply.github.com" `
    commit -m "Initial commit: Jingyu (Jing-Yu) - healing platform v1

5 phases delivered:
  Phase 1 - FastAPI + SQLite + Jinja2 SSR foundation
  Phase 2 - Guqin 5-yin healing music (16 tracks)
  Phase 3 - Encrypted diary bottles (end-to-end Fernet)
  Phase 4 - Mood checkin + spirit garden + shop
  Phase 5 - Secret admin backend (no public link, audit log)

Tech: FastAPI 0.115+, SQLAlchemy 2.0, Jinja2, bcrypt, Fernet
      (AES-128-CBC + HMAC), PBKDF2, itsdangerous, uvicorn" | Out-Null
Write-Host "      OK" -ForegroundColor Green

Write-Host "[5/6] gh repo create $RepoName (public) + push ..." -ForegroundColor Yellow
& $GhExe repo create $RepoName `
    --public `
    --source=. `
    --remote=origin `
    --push `
    --description $RepoDesc
Write-Host "      OK" -ForegroundColor Green

Write-Host "[6/6] Set topics ..." -ForegroundColor Yellow
& $GhExe repo edit $RepoName --add-topic $Topics
Write-Host "      OK" -ForegroundColor Green

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Done!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host ("Repo URL : https://github.com/sunday-lil/" + $RepoName) -ForegroundColor White
Write-Host ("Local    : " + $ProjectDir) -ForegroundColor White
Write-Host "Remote   : origin" -ForegroundColor White
Write-Host ""
Write-Host "Next steps you can run:"
Write-Host "  git log --oneline                       # view commit"
Write-Host "  git remote -v                           # view remote"
Write-Host ("  & '" + $GhExe + "' repo view --web    # open in browser")
Write-Host ""
