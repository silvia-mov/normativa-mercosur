# Convierte con Microsoft Word los .doc/.docx de resoluciones_gmc/ y directivas_ccm/ a texto UTF-8
# en texto_crudo/<carpeta>/<año>/<nombre>.txt. Se puede cortar y volver a correr: salta lo ya hecho.
# Equivale a scripts/a_texto_word.sh (LibreOffice) del repositorio, para Windows sin LibreOffice.
# Uso: powershell -ExecutionPolicy Bypass -File a_texto_word.ps1
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
$log = Join-Path $raiz 'texto_crudo\conversion_word.log'
New-Item -ItemType Directory -Force (Join-Path $raiz 'texto_crudo') | Out-Null

function Nuevo-Word {
    $w = New-Object -ComObject Word.Application
    $w.Visible = $false
    $w.DisplayAlerts = 0                 # wdAlertsNone
    $w.AutomationSecurity = 3            # msoAutomationSecurityForceDisable: sin macros
    $w.Options.ConfirmConversions = $false
    return $w
}

$word = Nuevo-Word
$hechos = 0; $errores = 0
foreach ($carpeta in 'resoluciones_gmc', 'directivas_ccm') {
    $archivos = Get-ChildItem -Recurse -File (Join-Path $raiz $carpeta) |
        Where-Object { $_.Extension -match '^\.docx?$' -and ($env:SOLO -eq $null -or $_.Name -like $env:SOLO) }
    foreach ($f in $archivos) {
        $anho = $f.Directory.Name
        $dest = Join-Path $raiz "texto_crudo\$carpeta\$anho\$($f.BaseName).txt"
        if ((Test-Path $dest) -and (Get-Item $dest).Length -gt 0) { continue }
        New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
        try {
            # Open(FileName, ConfirmConversions, ReadOnly, AddToRecentFiles)
            $doc = $word.Documents.Open($f.FullName, $false, $true, $false)
            # SaveAs2(FileName, FileFormat=wdFormatText(2), ..., Encoding=65001 UTF-8)
            $doc.SaveAs2([string]$dest, 2, $false, '', $false, '', $false, $false, $false, $false, $false, 65001)
            $doc.Close(0)
            $hechos++
        } catch {
            $errores++
            Add-Content -Encoding utf8 $log "$($f.FullName)`t$($_.Exception.Message)"
            try { $word.Quit([ref]0) } catch {}
            [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
            Get-Process WINWORD -ErrorAction SilentlyContinue | Stop-Process -Force
            $word = Nuevo-Word
        }
        if (($hechos + $errores) % 200 -eq 0) { Write-Output "$(Get-Date -Format T) $carpeta $anho : $hechos convertidos, $errores errores" }
    }
}
$word.Quit([ref]0)
Write-Output "FIN: $hechos convertidos, $errores errores"
