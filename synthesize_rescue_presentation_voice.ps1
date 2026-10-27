$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$productionRoot = Join-Path $PSScriptRoot 'tmp\rescue_presentation'
$plan = Get-Content -LiteralPath (Join-Path $productionRoot 'narration_plan.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.SelectVoice('Microsoft Haruka Desktop')
$speaker.Rate = 1
$speaker.Volume = 100
foreach ($clip in $plan) {
    $speaker.SetOutputToWaveFile((Join-Path $productionRoot $clip.file))
    $speaker.Speak($clip.text)
    $speaker.SetOutputToNull()
    Write-Output ('VOICE_COMPLETE ' + $clip.index)
}
$speaker.Dispose()
