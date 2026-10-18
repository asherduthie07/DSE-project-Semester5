# Clone-local Power BI setup. Requires Windows PowerShell 5.1+ or PowerShell 7.
[CmdletBinding()]
param(
    [switch]$ValidateOnly,
    [switch]$NoOpen,
    [string]$DataRoot
)
$ErrorActionPreference = 'Stop'
try {
    $repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
    $exports = Join-Path $repo 'powerbi\exports\v1'
    $manifestPath = Join-Path $exports 'manifest.json'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw "Missing export manifest: $manifestPath" }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.export_version -ne 'v1') { throw "Unsupported export version: $($manifest.export_version)" }
    $entries = @($manifest.files.PSObject.Properties)
    if ($entries.Count -ne 19) { throw "Expected 19 export CSVs; manifest lists $($entries.Count)" }
    foreach ($entry in $entries) {
        $file = Join-Path $exports $entry.Name
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing export: $file" }
        $hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($hash -ne $entry.Value.sha256.ToLowerInvariant()) { throw "Checksum mismatch: $file" }
        $header = (Get-Content -LiteralPath $file -TotalCount 1 -Encoding UTF8).TrimStart([char]0xFEFF)
        $expectedHeader = [string]::Join(',', [string[]]@($entry.Value.columns))
        if ($header -ne $expectedHeader) { throw "Header mismatch: $file" }
        $rows = @(Import-Csv -LiteralPath $file -Encoding UTF8).Count
        if ($rows -ne [int]$entry.Value.rows) { throw "Row-count mismatch: $file ($rows versus $($entry.Value.rows))" }
    }
    $source = Join-Path $repo 'powerbi\MediScopeAI.pbip'
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "PBIP source missing: $source" }
    if (-not $DataRoot) { $DataRoot = $exports }
    $DataRoot = (Resolve-Path -LiteralPath $DataRoot).Path
    if ($DataRoot -ne $exports) {
        foreach ($entry in $entries) {
            $file = Join-Path $DataRoot $entry.Name
            if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing configured data file: $file" }
            $hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($hash -ne $entry.Value.sha256.ToLowerInvariant()) { throw "Configured data file differs from bundled snapshot: $file" }
        }
    }
    if ($DataRoot -match '"') { throw 'DataRoot path cannot contain a double quote.' }
    $desktop = Get-Command 'PBIDesktop.exe' -ErrorAction SilentlyContinue
    $desktopPaths = @(
        "$env:ProgramFiles\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
        "${env:ProgramFiles(x86)}\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
    )
    if (-not $desktop) {
        foreach ($candidate in $desktopPaths) {
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { $desktop = $candidate; break }
        }
    }
    if (-not $desktop) {
        $storeApp = Get-AppxPackage -Name 'Microsoft.MicrosoftPowerBIDesktop' -ErrorAction SilentlyContinue
        if ($storeApp) { $desktop = $storeApp }
    }
    Write-Host "PASS: $($entries.Count) aggregate exports, schemas, row counts and SHA-256 checksums"
    Write-Host "Repository: $repo"
    Write-Host "Data root: $DataRoot"
    if ($ValidateOnly) {
        Write-Host 'Validation only: no local PBIP copy or Desktop launch attempted.'
        if (-not $desktop) { Write-Warning 'Power BI Desktop was not detected. Install it before opening the PBIP.' }
        exit 0
    }
    if (-not $desktop) { throw 'Power BI Desktop was not detected. Install the current Windows Power BI Desktop from Microsoft, then rerun this script.' }
    $local = Join-Path $repo 'powerbi\.local\MediScopeAI'
    New-Item -ItemType Directory -Path $local -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $repo 'powerbi\MediScopeAI.pbip') -Destination (Join-Path $local 'MediScopeAI.pbip') -Force
    foreach ($folder in @('MediScopeAI.Report', 'MediScopeAI.SemanticModel')) {
        $target = Join-Path $local $folder
        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
        Copy-Item -LiteralPath (Join-Path $repo "powerbi\$folder") -Destination $target -Recurse -Force
    }
    $parameterFile = Join-Path $local 'MediScopeAI.SemanticModel\definition\expressions.tmdl'
    $contents = Get-Content -LiteralPath $parameterFile -Raw -Encoding UTF8
    if (-not $contents.Contains('__MEDISCOPE_DATA_ROOT__')) { throw 'DataRoot token missing from local model copy.' }
    $escaped = $DataRoot.Replace('"', '""')
    [System.IO.File]::WriteAllText($parameterFile, $contents.Replace('__MEDISCOPE_DATA_ROOT__', $escaped), [System.Text.UTF8Encoding]::new($false))
    $ready = Join-Path $local 'MediScopeAI.pbip'
    Write-Host "Local PBIP: $ready"
    Write-Host 'Desktop may ask for file trust, data-source permission or refresh confirmation. Inspect all six pages and save a PBIX through Desktop File > Save As.'
    if (-not $NoOpen) { Start-Process -FilePath $ready }
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
