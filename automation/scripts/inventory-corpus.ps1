<#
.SYNOPSIS
  Creates a read-only local inventory for a private document corpus.

.DESCRIPTION
  This script scans file metadata without moving, renaming, copying or uploading
  original documents. It writes private inventory files to a local ignored folder.

  The output can contain sensitive file names. Do not commit generated files.

.PARAMETER SourcePath
  Local private corpus path to scan.

.PARAMETER OutputDir
  Local output directory. Defaults to ./local-index.

.EXAMPLE
  .\automation\scripts\inventory-corpus.ps1 -SourcePath "C:\chemin\vers\corpus-prive"
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidateNotNullOrEmpty()]
  [string]$SourcePath,

  [Parameter(Mandatory = $false)]
  [ValidateNotNullOrEmpty()]
  [string]$OutputDir = "local-index"
)

$ErrorActionPreference = "Stop"

function Get-NormalizedExtension {
  param([System.IO.FileInfo]$File)

  if ([string]::IsNullOrWhiteSpace($File.Extension)) {
    return "[sans extension]"
  }

  return $File.Extension.ToLowerInvariant()
}

function Get-RelativePathCompat {
  param(
    [Parameter(Mandatory = $true)]
    [string]$BasePath,

    [Parameter(Mandatory = $true)]
    [string]$TargetPath
  )

  $baseFull = [System.IO.Path]::GetFullPath($BasePath).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
  $targetFull = [System.IO.Path]::GetFullPath($TargetPath)
  $baseUri = New-Object System.Uri($baseFull)
  $targetUri = New-Object System.Uri($targetFull)
  $relativeUri = $baseUri.MakeRelativeUri($targetUri)
  $relative = [System.Uri]::UnescapeDataString($relativeUri.ToString())
  return $relative.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
}

function Get-ClassificationProposal {
  param([string]$RelativePath)

  $text = $RelativePath.ToLowerInvariant()

  $rules = @(
    @{ Category = "interessement / participation / epargne salariale"; Pattern = "interessement|participation|pee|pereco|epargne" },
    @{ Category = "remuneration et paie"; Pattern = "paie|salaire|remuneration|bulletin|nibelis" },
    @{ Category = "primes"; Pattern = "prime|ppv|partage de valeur" },
    @{ Category = "temps de travail"; Pattern = "temps de travail|horaire|horaires|travail" },
    @{ Category = "equipes postees / 5x8"; Pattern = "5x8|poste|postes|3x8|calendrier" },
    @{ Category = "astreinte"; Pattern = "astreinte" },
    @{ Category = "conges et repos"; Pattern = "conges|repos|cet|compte epargne temps" },
    @{ Category = "classifications"; Pattern = "classification|coefficient|reclassement|classe" },
    @{ Category = "emploi / competences / formation"; Pattern = "emploi|competence|formation|gepp|gpec" },
    @{ Category = "egalite professionnelle"; Pattern = "egalite professionnelle|egalite" },
    @{ Category = "sante securite conditions de travail"; Pattern = "sante|securite|cssct|conditions de travail|prevention" },
    @{ Category = "retraite / fin de carriere"; Pattern = "retraite|fin de carriere|prevoyance|mutuelle" },
    @{ Category = "dialogue social / CSE / droit syndical"; Pattern = "cse|irp|droit syndical|syndical|pap|vote electronique|dialogue social" },
    @{ Category = "avenants"; Pattern = "avenant" },
    @{ Category = "accords entreprise"; Pattern = "accord|protocole" }
  )

  $matches = @($rules | Where-Object { $text -match $_.Pattern } | ForEach-Object { $_.Category } | Select-Object -Unique)

  if ($matches.Count -eq 1) {
    return @{
      categorieProposee = $matches[0]
      confiance = "moyenne"
      remarque = "Classement propose uniquement a partir du nom du fichier. Verification humaine necessaire avant validation."
    }
  }

  if ($matches.Count -gt 1) {
    return @{
      categorieProposee = "A CLASSER - VERIFICATION HUMAINE NECESSAIRE"
      confiance = "faible"
      remarque = "Plusieurs categories possibles detectees a partir du nom du fichier."
    }
  }

  return @{
    categorieProposee = "autres / a classer"
    confiance = "faible"
    remarque = "Aucun signal suffisamment clair dans le nom du fichier. Verification humaine necessaire."
  }
}

function New-SafeOutputName {
  param([string]$Prefix, [string]$Extension)

  $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
  return "$Prefix-$timestamp.private.$Extension"
}

$source = Get-Item -LiteralPath $SourcePath
if (-not $source.PSIsContainer) {
  throw "SourcePath must be a directory."
}

$sourceFullPath = $source.FullName
$outputFullPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputDir))
New-Item -ItemType Directory -Force -Path $outputFullPath | Out-Null

$files = @(Get-ChildItem -LiteralPath $sourceFullPath -File -Recurse -Force -ErrorAction SilentlyContinue)
$directories = @(Get-ChildItem -LiteralPath $sourceFullPath -Directory -Recurse -Force -ErrorAction SilentlyContinue)
$unreadable = New-Object System.Collections.Generic.List[object]

$inventory = foreach ($file in $files) {
  $relativePath = Get-RelativePathCompat -BasePath $sourceFullPath -TargetPath $file.FullName
  $relativeDirectory = Split-Path -Parent $relativePath
  if ([string]::IsNullOrWhiteSpace($relativeDirectory)) {
    $relativeDirectory = "[racine]"
  }

  $hash = $null
  $readStatus = "ok"
  $readError = $null

  try {
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  } catch {
    $readStatus = "hash impossible"
    $readError = $_.Exception.Message
    $unreadable.Add([pscustomobject]@{
      extension = Get-NormalizedExtension -File $file
      relativePath = $relativePath
      status = $readStatus
      error = $readError
    }) | Out-Null
  }

  $classification = Get-ClassificationProposal -RelativePath $relativePath

  [pscustomobject]@{
    nomFichier = $file.Name
    extension = Get-NormalizedExtension -File $file
    tailleOctets = $file.Length
    dateModification = $file.LastWriteTime.ToString("o")
    cheminRelatif = $relativePath
    sousDossier = $relativeDirectory
    sha256 = $hash
    lecture = $readStatus
    categorieProposee = $classification.categorieProposee
    confianceClassement = $classification.confiance
    remarqueClassement = $classification.remarque
  }
}

$duplicates = @(
  $inventory |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_.sha256) } |
    Group-Object sha256 |
    Where-Object { $_.Count -gt 1 }
)

$extensionSummary = @(
  $inventory |
    Group-Object extension |
    Sort-Object Count -Descending |
    ForEach-Object {
      [pscustomobject]@{
        extension = $_.Name
        count = $_.Count
      }
    }
)

$subfolderSummary = @(
  $inventory |
    Group-Object sousDossier |
    Sort-Object Count -Descending |
    ForEach-Object {
      [pscustomobject]@{
        sousDossier = $_.Name
        count = $_.Count
      }
    }
)

$classificationSummary = @(
  $inventory |
    Group-Object categorieProposee |
    Sort-Object Count -Descending |
    ForEach-Object {
      [pscustomobject]@{
        categorie = $_.Name
        count = $_.Count
      }
    }
)

$unusualFormats = @(
  $inventory |
    Where-Object { $_.extension -notin @(".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".rtf", ".odt", ".ods") } |
    Group-Object extension |
    Sort-Object Count -Descending |
    ForEach-Object {
      [pscustomobject]@{
        extension = $_.Name
        count = $_.Count
      }
    }
)

$summary = [pscustomobject]@{
  generatedAt = (Get-Date).ToString("o")
  sourcePathStored = $false
  sourceLabel = "private-local-corpus"
  totalFiles = $inventory.Count
  hasSubfolders = ($directories.Count -gt 0)
  subfolderCount = $directories.Count
  extensions = $extensionSummary
  filesBySubfolder = $subfolderSummary
  exactDuplicateGroups = $duplicates.Count
  exactDuplicateFiles = (($duplicates | ForEach-Object { $_.Count }) | Measure-Object -Sum).Sum
  unreadableFiles = $unreadable.Count
  unusualFormats = $unusualFormats
  classificationProposal = $classificationSummary
  securityNotice = "Generated inventory is private and must not be committed."
}

$jsonPath = Join-Path $outputFullPath (New-SafeOutputName -Prefix "corpus-inventory" -Extension "json")
$csvPath = Join-Path $outputFullPath (New-SafeOutputName -Prefix "corpus-inventory" -Extension "csv")
$summaryPath = Join-Path $outputFullPath (New-SafeOutputName -Prefix "corpus-summary" -Extension "json")

$inventory | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jsonPath -Encoding UTF8
$inventory | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-Output "Inventory completed."
Write-Output "Total files: $($summary.totalFiles)"
Write-Output "Exact duplicate groups: $($summary.exactDuplicateGroups)"
Write-Output "Unreadable files: $($summary.unreadableFiles)"
Write-Output "Private output directory: $OutputDir"
Write-Output "Generated files are ignored by Git and must stay local."
