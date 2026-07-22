[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [string]$SourceRoot = (Join-Path $PSScriptRoot '..\..'),
    [string[]]$TargetRoots = @(
        'C:\Users\NITRO\.agents\skills',
        'C:\Users\NITRO\.claude\skills',
        'C:\Users\NITRO\.gemini\skills',
        'C:\Users\NITRO\.gemini\antigravity\skills'
    ),
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SkillNames = @(
    'ai-product-evaluation',
    'ai-eval-dataset-governance',
    'healthcare-rag-graph-ocr-evaluation'
)

function Assert-AbsolutePath {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Label)

    if (-not [System.IO.Path]::IsPathRooted($Path)) {
        throw "$Label must be an absolute path: $Path"
    }
}

function Resolve-ExistingPath {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Label)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Label does not exist: $Path"
    }

    return (Resolve-Path -LiteralPath $Path).Path
}

function Test-CompatibleJunction {
    param(
        [Parameter(Mandatory)]$Item,
        [Parameter(Mandatory)][string]$ExpectedTarget
    )

    if ($Item.LinkType -ne 'Junction') {
        return $false
    }

    $junctionTarget = @($Item.Target)[0]
    if ([string]::IsNullOrWhiteSpace($junctionTarget) -or -not (Test-Path -LiteralPath $junctionTarget)) {
        return $false
    }

    $actualTarget = (Resolve-Path -LiteralPath $junctionTarget).Path
    return [string]::Equals($actualTarget, $ExpectedTarget, [System.StringComparison]::OrdinalIgnoreCase)
}

Assert-AbsolutePath -Path $SourceRoot -Label 'SourceRoot'
$resolvedSourceRoot = Resolve-ExistingPath -Path $SourceRoot -Label 'SourceRoot'

foreach ($targetRoot in $TargetRoots) {
    Assert-AbsolutePath -Path $targetRoot -Label 'TargetRoot'
}

foreach ($skill in $SkillNames) {
    $sourcePath = Join-Path $resolvedSourceRoot $skill
    $resolvedSourcePath = Resolve-ExistingPath -Path $sourcePath -Label "Source package '$skill'"
    if (-not (Test-Path -LiteralPath (Join-Path $resolvedSourcePath 'SKILL.md') -PathType Leaf)) {
        throw "Source package '$skill' is missing SKILL.md: $resolvedSourcePath"
    }

    foreach ($targetRoot in $TargetRoots) {
        $targetPath = Join-Path $targetRoot $skill
        if (Test-Path -LiteralPath $targetPath) {
            $existingItem = Get-Item -LiteralPath $targetPath -Force
            if (Test-CompatibleJunction -Item $existingItem -ExpectedTarget $resolvedSourcePath) {
                Write-Verbose "Compatible junction already exists: $targetPath"
                continue
            }

            if ($existingItem.PSIsContainer -and $existingItem.LinkType -ne 'Junction') {
                throw "Refusing to replace non-junction directory: $targetPath"
            }

            throw "Refusing to replace existing path that is not a compatible junction: $targetPath"
        }

        if ($DryRun) {
            Write-Output "DRY RUN: create junction '$targetPath' -> '$resolvedSourcePath'"
            continue
        }

        if ($PSCmdlet.ShouldProcess($targetPath, "Create junction to $resolvedSourcePath")) {
            New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
            New-Item -ItemType Junction -Path $targetPath -Target $resolvedSourcePath | Out-Null
            Write-Output "Created junction '$targetPath' -> '$resolvedSourcePath'"
        }
    }
}
