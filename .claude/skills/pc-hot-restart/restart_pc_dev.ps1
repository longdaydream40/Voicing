# Voice Coding PC dev hot-restart script
# Kills existing dev process (voice_coding.py) and restarts it.

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    $root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
    return $root.Path
}

function Resolve-PythonCommand {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py"
    }
    throw "Python not found in PATH. Please install Python or add it to PATH."
}

$repoRoot = Resolve-RepoRoot
$pcDir = Join-Path $repoRoot "pc"
$entry = Join-Path $pcDir "voice_coding.py"

if (-not (Test-Path $entry)) {
    throw "Entry file not found: $entry"
}

# Kill existing dev Python process running voice_coding.py
Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.CommandLine -match "voice_coding\.py"
} | ForEach-Object {
    try {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
    } catch {
        Write-Host "Failed to stop PID $($_.ProcessId): $($_.Exception.Message)"
    }
}

# Also stop packaged exe variants if they are running (best-effort)
@("VoiceCoding", "voicing-windows-x64") | ForEach-Object {
    $processName = $_
    Get-Process -Name $processName -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            Stop-Process -Id $_.Id -Force -ErrorAction Stop
        } catch {
            Write-Host "Failed to stop $processName PID $($_.Id): $($_.Exception.Message)"
        }
    }
}

$pythonCmd = Resolve-PythonCommand
$arguments = @("`"$entry`"", "--dev")

Start-Process -FilePath $pythonCmd -ArgumentList $arguments -WorkingDirectory $pcDir -WindowStyle Hidden
Write-Host "Restarted dev app: $entry"
