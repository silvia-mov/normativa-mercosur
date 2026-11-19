# OCR de los PDF escaneados de resoluciones_gmc/ y directivas_ccm/ con el OCR de Windows (español).
# Equivale a scripts/b_ocr_pdf.sh (Tesseract) del repositorio, para Windows sin Tesseract.
# Solo procesa los PDF cuyo texto (texto_crudo/.../<nombre>.pdf.txt) quedó casi vacío con pdftotext.
# Uso: powershell -ExecutionPolicy Bypass -File b_ocr_pdf.ps1
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[void][Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
[void][Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
[void][Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
[void][Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
[void][Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]

$asTaskGen = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
$asTaskAction = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' })[0]
function Esperar($op, [Type]$tipo) {
    $t = $asTaskGen.MakeGenericMethod($tipo).Invoke($null, @($op)); $t.Wait(-1) | Out-Null; $t.Result
}
function EsperarAccion($op) { $t = $asTaskAction.Invoke($null, @($op)); $t.Wait(-1) | Out-Null }

$ocr = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('es-ES'))
foreach ($carpeta in 'resoluciones_gmc', 'directivas_ccm') {
    foreach ($f in Get-ChildItem -Recurse -File -Filter *.pdf (Join-Path $raiz $carpeta)) {
        $dest = Join-Path $raiz "texto_crudo\$carpeta\$($f.Directory.Name)\$($f.BaseName).pdf.txt"
        if ((Test-Path $dest) -and (Get-Content -Raw -Encoding utf8 $dest).Trim().Length -gt 200) { continue }
        $archivo = Esperar ([Windows.Storage.StorageFile]::GetFileFromPathAsync($f.FullName)) ([Windows.Storage.StorageFile])
        $pdf = Esperar ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($archivo)) ([Windows.Data.Pdf.PdfDocument])
        $partes = New-Object System.Collections.Generic.List[string]
        for ($i = 0; $i -lt $pdf.PageCount; $i++) {
            $pag = $pdf.GetPage($i)
            $opc = [Windows.Data.Pdf.PdfPageRenderOptions]::new()
            $opc.DestinationWidth = [uint32]([Math]::Min(2400, $pag.Size.Width * 200 / 72))   # ~200 ppp
            $flujo = [Windows.Storage.Streams.InMemoryRandomAccessStream]::new()
            EsperarAccion ($pag.RenderToStreamAsync($flujo, $opc))
            $dec = Esperar ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($flujo)) ([Windows.Graphics.Imaging.BitmapDecoder])
            $bmp = Esperar ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
            $res = Esperar ($ocr.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
            $partes.Add("[página $($i + 1)]")
            foreach ($l in $res.Lines) { $partes.Add($l.Text) }
            $bmp.Dispose(); $flujo.Dispose(); $pag.Dispose()
        }
        New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
        [IO.File]::WriteAllText($dest, ($partes -join "`n") + "`n", [Text.UTF8Encoding]::new($false))
        Write-Output "$(Get-Date -Format T) $($f.Name): $($pdf.PageCount) páginas"
    }
}
Write-Output 'FIN'
