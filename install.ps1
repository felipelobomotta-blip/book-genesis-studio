# Install the Book Genesis skills for one agent.
# Usage: .\install.ps1 -Target claude [-Destination PATH] [-AgentsDestination PATH] [-DryRun] [-Force]
# List targets with: python runner\installer.py targets
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Target,
    [string]$Destination = "",
    [string]$AgentsDestination = "",
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$cliPath = Join-Path $repoDir "runner\installer.py"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$launcherArgs = @()
if (-not $pythonCommand) {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    $launcherArgs = @("-3")
}
if (-not $pythonCommand) {
    throw "Python 3.10 or newer was not found in PATH."
}

$cliArgs = @($cliPath, "install", $Target)
if ($Destination) { $cliArgs += @("--dest", $Destination) }
if ($AgentsDestination) { $cliArgs += @("--agents-dest", $AgentsDestination) }
if ($Force) { $cliArgs += "--force" }
if ($DryRun) { $cliArgs += "--dry-run" }

& $pythonCommand.Source @launcherArgs @cliArgs
exit $LASTEXITCODE
