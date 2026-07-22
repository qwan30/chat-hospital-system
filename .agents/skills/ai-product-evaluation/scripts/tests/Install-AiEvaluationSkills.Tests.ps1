$ErrorActionPreference = 'Stop'

$installer = Join-Path $PSScriptRoot '..\Install-AiEvaluationSkills.ps1'

function New-SkillSourceFixture {
    param([Parameter(Mandatory)][string]$Root)

    foreach ($skill in @(
        'ai-product-evaluation',
        'ai-eval-dataset-governance',
        'healthcare-rag-graph-ocr-evaluation'
    )) {
        $skillPath = Join-Path $Root $skill
        New-Item -ItemType Directory -Path $skillPath -Force | Out-Null
        Set-Content -LiteralPath (Join-Path $skillPath 'SKILL.md') -Value "---`nname: $skill`ndescription: fixture`n---"
    }
}

function Invoke-ExpectFailure {
    param(
        [Parameter(Mandatory)][scriptblock]$Operation,
        [Parameter(Mandatory)][string]$MessagePattern
    )

    $caught = $null
    try {
        & $Operation
    }
    catch {
        $caught = $_
    }

    ($null -ne $caught) | Should Be $true
    $caught.Exception.Message | Should Match $MessagePattern
}

Describe 'Install-AiEvaluationSkills' {
    BeforeEach {
        $testRoot = Join-Path $TestDrive ([guid]::NewGuid().ToString())
        $sourceRoot = Join-Path $testRoot 'source'
        $targetRoot = Join-Path $testRoot 'targets'
        New-SkillSourceFixture -Root $sourceRoot
    }

    It 'creates each requested target junction from a valid source package' {
        & $installer -SourceRoot $sourceRoot -TargetRoots @($targetRoot)

        foreach ($skill in @(
            'ai-product-evaluation',
            'ai-eval-dataset-governance',
            'healthcare-rag-graph-ocr-evaluation'
        )) {
            $target = Join-Path $targetRoot $skill
            (Test-Path -LiteralPath $target) | Should Be $true
            (Get-Item -LiteralPath $target).LinkType | Should Be 'Junction'
        }
    }

    It 'accepts a compatible existing junction without replacing it' {
        $skill = 'ai-product-evaluation'
        $source = Join-Path $sourceRoot $skill
        $target = Join-Path $targetRoot $skill
        New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
        New-Item -ItemType Junction -Path $target -Target $source | Out-Null

        & $installer -SourceRoot $sourceRoot -TargetRoots @($targetRoot)

        $junction = Get-Item -LiteralPath $target
        $junction.LinkType | Should Be 'Junction'
        (Resolve-Path -LiteralPath @($junction.Target)[0]).Path | Should Be (Resolve-Path -LiteralPath $source).Path
    }

    It 'refuses to replace a non-junction directory' {
        $target = Join-Path $targetRoot 'ai-product-evaluation'
        New-Item -ItemType Directory -Path $target -Force | Out-Null

        Invoke-ExpectFailure -Operation {
            & $installer -SourceRoot $sourceRoot -TargetRoots @($targetRoot)
        } -MessagePattern 'non-junction directory'
    }

    It 'rejects a relative target root before changing the filesystem' {
        Invoke-ExpectFailure -Operation {
            & $installer -SourceRoot $sourceRoot -TargetRoots @('relative-target')
        } -MessagePattern 'absolute path'
    }

    It 'rejects a target root nested under the protected Codex skills directory' {
        Invoke-ExpectFailure -Operation {
            & $installer -SourceRoot $sourceRoot -TargetRoots @('C:\Users\NITRO\.codex\skills\nested-target')
        } -MessagePattern 'protected Codex skills directory'
    }

    It 'rejects the protected Codex skills directory as a target root' {
        Invoke-ExpectFailure -Operation {
            & $installer -SourceRoot $sourceRoot -TargetRoots @('C:\Users\NITRO\.codex\skills')
        } -MessagePattern 'protected Codex skills directory'
    }

    It 'rejects a junction target root that aliases the protected Codex skills directory' {
        $protectedAlias = Join-Path $testRoot 'protected-alias'
        New-Item -ItemType Junction -Path $protectedAlias -Target 'C:\Users\NITRO\.codex\skills' | Out-Null

        Invoke-ExpectFailure -Operation {
            & $installer -SourceRoot $sourceRoot -TargetRoots @($protectedAlias) -DryRun
        } -MessagePattern 'reparse point'
    }

    It 'rejects a Windows root-relative target root before changing the filesystem' {
        Invoke-ExpectFailure -Operation {
            & $installer -SourceRoot $sourceRoot -TargetRoots @('\rooted-but-not-fully-qualified')
        } -MessagePattern 'fully qualified.*path'
    }

    It 'does not create earlier junctions when a later target path collides' {
        $laterCollision = Join-Path $targetRoot 'healthcare-rag-graph-ocr-evaluation'
        New-Item -ItemType Directory -Path $laterCollision -Force | Out-Null

        Invoke-ExpectFailure -Operation {
            & $installer -SourceRoot $sourceRoot -TargetRoots @($targetRoot)
        } -MessagePattern 'non-junction directory'

        (Test-Path -LiteralPath (Join-Path $targetRoot 'ai-product-evaluation')) | Should Be $false
        (Test-Path -LiteralPath (Join-Path $targetRoot 'ai-eval-dataset-governance')) | Should Be $false
    }

    It 'rejects duplicate target roots before creating any junctions' {
        Invoke-ExpectFailure -Operation {
            & $installer -SourceRoot $sourceRoot -TargetRoots @($targetRoot, $targetRoot)
        } -MessagePattern 'duplicate target root'

        (Test-Path -LiteralPath (Join-Path $targetRoot 'ai-product-evaluation')) | Should Be $false
    }

    It 'derives default target roots from the current user profile API' {
        $installerContent = Get-Content -LiteralPath $installer -Raw

        $installerContent | Should Match 'GetFolderPath\(\[System\.Environment\+SpecialFolder\]::UserProfile\)'
        $installerContent | Should Not Match 'C:\\Users\\NITRO\\\.(agents|claude|gemini)'
    }
}
