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

function ConvertTo-NormalizedPath {
    param([Parameter(Mandatory)][string]$Path)

    $pathWithoutDevicePrefix = $Path
    if ($pathWithoutDevicePrefix.StartsWith('\\?\UNC\', [System.StringComparison]::OrdinalIgnoreCase)) {
        $pathWithoutDevicePrefix = '\\' + $pathWithoutDevicePrefix.Substring(8)
    }
    elseif (
        $pathWithoutDevicePrefix.StartsWith('\\?\', [System.StringComparison]::OrdinalIgnoreCase) -or
        $pathWithoutDevicePrefix.StartsWith('\\.\', [System.StringComparison]::OrdinalIgnoreCase)
    ) {
        $pathWithoutDevicePrefix = $pathWithoutDevicePrefix.Substring(4)
    }

    return [System.IO.Path]::GetFullPath($pathWithoutDevicePrefix).TrimEnd('\', '/')
}

function Test-PathOverlap {
    param(
        [Parameter(Mandatory)][string]$FirstPath,
        [Parameter(Mandatory)][string]$SecondPath
    )

    return (
        [string]::Equals($FirstPath, $SecondPath, [System.StringComparison]::OrdinalIgnoreCase) -or
        $FirstPath.StartsWith("$SecondPath\", [System.StringComparison]::OrdinalIgnoreCase) -or
        $SecondPath.StartsWith("$FirstPath\", [System.StringComparison]::OrdinalIgnoreCase)
    )
}

function Assert-SafeTargetRoot {
    param([Parameter(Mandatory)][string]$Path)

    Assert-AbsolutePath -Path $Path -Label 'TargetRoot'

    $normalizedTargetRoot = ConvertTo-NormalizedPath -Path $Path
    $normalizedProtectedRoot = ConvertTo-NormalizedPath -Path $ProtectedCodexSkillsRoot
    if (Test-PathOverlap -FirstPath $normalizedTargetRoot -SecondPath $normalizedProtectedRoot) {
        throw "TargetRoot must not equal or be nested under the protected Codex skills directory: $Path"
    }

    $existingAncestorPath = $Path
    $existingAncestor = $null
    while ($null -eq $existingAncestor) {
        $existingAncestor = Get-Item -LiteralPath $existingAncestorPath -Force -ErrorAction SilentlyContinue
        if ($null -ne $existingAncestor) {
            break
        }

        $parentPath = Split-Path -Path $existingAncestorPath -Parent
        if ([string]::Equals($parentPath, $existingAncestorPath, [System.StringComparison]::OrdinalIgnoreCase)) {
            break
        }

        $existingAncestorPath = $parentPath
    }

    if ($null -ne $existingAncestor -and -not [string]::IsNullOrWhiteSpace($existingAncestor.LinkType)) {
        throw "TargetRoot must not use a reparse point: $Path"
    }

    return $normalizedTargetRoot
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

$resolvedSourcePackages = @{}
foreach ($skill in $SkillNames) {
    $sourcePath = Join-Path $resolvedSourceRoot $skill
    $resolvedSourcePath = Resolve-ExistingPath -Path $sourcePath -Label "Source package '$skill'"
    if (-not (Test-Path -LiteralPath (Join-Path $resolvedSourcePath 'SKILL.md') -PathType Leaf)) {
        throw "Source package '$skill' is missing SKILL.md: $resolvedSourcePath"
    }

    $resolvedSourcePackages[$skill] = $resolvedSourcePath
}

if ($TargetRoots.Count -eq 0) {
    $TargetRoots = Get-DefaultTargetRoots
}

$normalizedTargetRoots = @{}
$validatedTargetRoots = @()
foreach ($targetRoot in $TargetRoots) {
    $normalizedTargetRoot = Assert-SafeTargetRoot -Path $targetRoot

    if (Test-PathOverlap -FirstPath $normalizedTargetRoot -SecondPath $resolvedSourceRoot) {
        throw "TargetRoot must not overlap a source path: $targetRoot"
    }

    foreach ($resolvedSourcePath in $resolvedSourcePackages.Values) {
        if (Test-PathOverlap -FirstPath $normalizedTargetRoot -SecondPath $resolvedSourcePath) {
            throw "TargetRoot must not overlap a source path: $targetRoot"
        }
    }

    $targetRootKey = $normalizedTargetRoot.ToUpperInvariant()
    if ($normalizedTargetRoots.ContainsKey($targetRootKey)) {
        throw "TargetRoots contains duplicate target root: $targetRoot"
    }

    foreach ($existingTargetRoot in $validatedTargetRoots) {
        if (Test-PathOverlap -FirstPath $normalizedTargetRoot -SecondPath $existingTargetRoot) {
            throw "TargetRoots must not overlap by ancestry: $targetRoot"
        }
    }

    $normalizedTargetRoots[$targetRootKey] = $true
    $validatedTargetRoots += $normalizedTargetRoot
}
$TargetRoots = $validatedTargetRoots

$installPlans = @()
foreach ($skill in $SkillNames) {
    $resolvedSourcePath = $resolvedSourcePackages[$skill]

    foreach ($targetRoot in $TargetRoots) {
        $targetPath = Join-Path $targetRoot $skill
        $normalizedTargetPath = ConvertTo-NormalizedPath -Path $targetPath
        if (
            (Test-PathOverlap -FirstPath $normalizedTargetPath -SecondPath $resolvedSourceRoot) -or
            (Test-PathOverlap -FirstPath $normalizedTargetPath -SecondPath $resolvedSourcePath)
        ) {
            throw "Planned destination must not overlap a source path: $targetPath"
        }

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
