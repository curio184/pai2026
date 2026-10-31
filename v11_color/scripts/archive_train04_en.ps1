$ErrorActionPreference = 'Stop'
$workRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$sourceRoot = (Resolve-Path -LiteralPath (Join-Path $workRoot 'models')).Path
$archiveRoot = 'C:\Temp\pai2026_model_archive\v11_color\models'
$report = Join-Path $workRoot 'reports\model_archive_train04_en_20261029.json'
if (Test-Path -LiteralPath $report) { throw 'Archive report already exists; inspect before retrying.' }
New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null
$archiveRoot = (Resolve-Path -LiteralPath $archiveRoot).Path
$entries = @()
foreach ($name in @('train04_en')) {
    $source = (Resolve-Path -LiteralPath (Join-Path $sourceRoot $name)).Path
    $target = Join-Path $archiveRoot $name
    if ($source -ne (Join-Path $sourceRoot $name)) { throw 'Unexpected source path.' }
    if (-not $source.StartsWith($sourceRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Source outside model workspace.' }
    if (-not $target.StartsWith($archiveRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Target outside approved archive.' }
    if ((Get-Item -LiteralPath $source).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Source already a reparse point.' }
    if (Test-Path -LiteralPath $target) { throw 'Archive target already exists; inspect before retrying.' }
    $files = @(Get-ChildItem -LiteralPath $source -File -Recurse)
    if (@(Get-ChildItem -LiteralPath $source -Recurse | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw 'Nested reparse point.' }
    $before = @($files | ForEach-Object {
        [pscustomobject]@{path=$_.FullName.Substring($source.Length+1);bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
    })
    Copy-Item -LiteralPath $source -Destination $target -Recurse
    if ((Get-ChildItem -LiteralPath $target -File -Recurse).Count -ne $before.Count) { throw 'File count mismatch.' }
    foreach ($f in $before) {
        $copied = Join-Path $target $f.path
        if ((Get-Item -LiteralPath $copied).Length -ne $f.bytes) { throw 'Length mismatch.' }
        if ((Get-FileHash -LiteralPath $copied -Algorithm SHA256).Hash.ToLowerInvariant() -ne $f.sha256) { throw 'Copy hash mismatch.' }
        if ((Get-FileHash -LiteralPath (Join-Path $source $f.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $f.sha256) { throw 'Source changed during copy.' }
    }
    $entry = [pscustomobject]@{name=$name;source=$source;archive=$target;copied_and_verified_utc=[DateTime]::UtcNow.ToString('o');files=$before;state='copy_verified'}
    $entries += $entry
    $entries | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $report -Encoding UTF8
    # Absolute source was checked against the explicitly approved train04_en model directory.
    # Every byte remains in the verified archive before this source copy is removed.
    if ((Resolve-Path -LiteralPath $source).Path -ne (Join-Path $sourceRoot $name)) { throw 'Source changed before removal.' }
    Remove-Item -LiteralPath $source -Recurse -Force
    New-Item -ItemType Junction -Path $source -Target $target | Out-Null
    foreach ($f in $before) {
        if ((Get-FileHash -LiteralPath (Join-Path $source $f.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $f.sha256) { throw 'Junction verification failed.' }
    }
    $entry.state = 'junction_verified'
    $entries | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $report -Encoding UTF8
    [pscustomobject]@{name=$name;files=$before.Count;bytes=($before | Measure-Object bytes -Sum).Sum;state=$entry.state}
}
Get-PSDrive D | Select-Object Name,Free


