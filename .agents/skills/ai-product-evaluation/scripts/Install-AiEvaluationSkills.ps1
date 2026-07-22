[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [string]$SourceRoot = (Join-Path $PSScriptRoot '..\..'),
    [string[]]$TargetRoots = @(),
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SkillNames = @(
    'ai-product-evaluation',
    'ai-eval-dataset-governance',
    'healthcare-rag-graph-ocr-evaluation'
)

$ProtectedCodexSkillsRoot = 'C:\Users\NITRO\.codex\skills'

function Get-DefaultTargetRoots {
    $userProfile = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
    return @(
        (Join-Path $userProfile '.agents\skills'),
        (Join-Path $userProfile '.claude\skills'),
        (Join-Path $userProfile '.gemini\skills'),
        (Join-Path $userProfile '.gemini\antigravity\skills')
    )
}

function Assert-AbsolutePath {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Label)

    if (-not [System.IO.Path]::IsPathFullyQualified($Path)) {
        throw "$Label must be a fully qualified absolute path: $Path"
    }
}

function Assert-SafeTargetRoot {
    param([Parameter(Mandatory)][string]$Path)

    Assert-AbsolutePath -Path $Path -Label 'TargetRoot'

    $normalizedTargetRoot = [System.IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
    $normalizedProtectedRoot = [System.IO.Path]::GetFullPath($ProtectedCodexSkillsRoot).TrimEnd('\', '/')
    if (
        [string]::Equals($normalizedTargetRoot, $normalizedProtectedRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
        $normalizedTargetRoot.StartsWith("$normalizedProtectedRoot\", [System.StringComparison]::OrdinalIgnoreCase)
    ) {
        throw "TargetRoot must not equal or be nested under the protected Codex skills directory: $Path"
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

function Get-ExistingTargetItem {
    param([Parameter(Mandatory)][string]$Path)

    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if ($null -ne $item) {
        return $item
    }

    $parentPath = Split-Path -Path $Path -Parent
    $leafName = Split-Path -Path $Path -Leaf
    if (Test-Path -LiteralPath $parentPath) {
        $childItems = @(Get-ChildItem -LiteralPath $parentPath -Force | Where-Object { $_.Name -eq $leafName })
        if ($childItems.Count -gt 0) {
            return $childItems[0]
        }
    }
}

Assert-AbsolutePath -Path $SourceRoot -Label 'SourceRoot'
$resolvedSourceRoot = Resolve-ExistingPath -Path $SourceRoot -Label 'SourceRoot'

if ($TargetRoots.Count -eq 0) {
    $TargetRoots = Get-DefaultTargetRoots
}

foreach ($targetRoot in $TargetRoots) {
    Assert-SafeTargetRoot -Path $targetRoot
}

$installPlans = @()
foreach ($skill in $SkillNames) {
    $sourcePath = Join-Path $resolvedSourceRoot $skill
    $resolvedSourcePath = Resolve-ExistingPath -Path $sourcePath -Label "Source package '$skill'"
    if (-not (Test-Path -LiteralPath (Join-Path $resolvedSourcePath 'SKILL.md') -PathType Leaf)) {
        throw "Source package '$skill' is missing SKILL.md: $resolvedSourcePath"
    }

    foreach ($targetRoot in $TargetRoots) {
        $targetPath = Join-Path $targetRoot $skill
        $existingItem = Get-ExistingTargetItem -Path $targetPath
        if ($null -ne $existingItem) {
            if (Test-CompatibleJunction -Item $existingItem -ExpectedTarget $resolvedSourcePath) {
                Write-Verbose "Compatible junction already exists: $targetPath"
                continue
            }

            if ($existingItem.PSIsContainer -and $existingItem.LinkType -ne 'Junction') {
                throw "Refusing to replace non-junction directory: $targetPath"
            }

            throw "Refusing to replace existing path that is not a compatible junction: $targetPath"
        }

        $installPlans += [pscustomobject]@{
            TargetRoot = $targetRoot
            TargetPath = $targetPath
            SourcePath = $resolvedSourcePath
        }
    }
}

foreach ($installPlan in $installPlans) {
    $targetRoot = $installPlan.TargetRoot
    $targetPath = $installPlan.TargetPath
    $resolvedSourcePath = $installPlan.SourcePath
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
