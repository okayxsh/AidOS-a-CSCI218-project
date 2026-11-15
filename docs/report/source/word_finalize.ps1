param(
  [Parameter(Mandatory=$true)][string]$InDocx,
  [Parameter(Mandatory=$true)][string]$OutDocx,
  [Parameter(Mandatory=$true)][string]$OutPdf
)
# Opens a generated .docx in Word, updates every field and table of contents,
# saves it as a normal .docx and exports a PDF preview.
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  $doc = $word.Documents.Open($InDocx, $false, $false, $false)
  $doc.Repaginate()
  foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
  $null = $doc.Fields.Update()
  foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
  foreach ($s in $doc.Sections) {
    foreach ($h in $s.Headers) { $null = $h.Range.Fields.Update() }
    foreach ($f in $s.Footers) { $null = $f.Range.Fields.Update() }
  }
  # 16 = wdFormatDocumentDefault (.docx)
  $doc.SaveAs2($OutDocx, 16)
  # 17 = wdExportFormatPDF; bookmarks from headings = 1
  $doc.ExportAsFixedFormat($OutPdf, 17, $false, 0, 0, 0, 0, 0, $true, $true, 1)
  $pages = $doc.ComputeStatistics(2)
  Write-Output "pages=$pages"
  $doc.Close($false)
} finally {
  $word.Quit()
  [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
