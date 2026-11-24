<#
.SYNOPSIS
  Installiert den Creo-MCP-Server unter Windows und richtet CREOSON, das Creo-Startskript und Claude Desktop ein.

.DESCRIPTION
  1. Python-Umgebung (.venv) im Ordner Creo_MCP anlegen und das Paket installieren
  2. CREOSON 3.0.2 herunterladen, SHA256 prüfen, entpacken (Standard C:\Creoson_<Benutzer>, nur für dich beschreibbar)
  3. setvars.bat (für creoson_run.bat) und nitro_proe_remote.bat (Creo-Start mit PRO_COMM_MSG_EXE) schreiben
  4. PRO_COMM_MSG_EXE dauerhaft für den Benutzer setzen (dann ist auch ein normal gestartetes Creo erreichbar)
  5. Eintrag "creo" in %APPDATA%\Claude\claude_desktop_config.json (Sicherung .bak, UTF-8 ohne BOM)

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\install_windows.ps1
  powershell -ExecutionPolicy Bypass -File scripts\install_windows.ps1 -WorkDir "D:\Schule\Creo" -SkipClaudeConfig
#>
param(
  # Ohne Leerzeichen (CREOSON startet das Startskript per Runtime.exec, Leerzeichen brechen den Pfad)
  # und pro Benutzer; der Ordner wird unten für andere Benutzer gesperrt.
  [string]$CreosonDir = ("C:\Creoson_" + ($env:USERNAME -replace '[^A-Za-z0-9_-]', '')),
  [string]$WorkDir = "$env:USERPROFILE\Documents\Creo",
  [int]$Port = 9056,
  [switch]$SkipCreoson,
  [switch]$SkipClaudeConfig,
  [switch]$NoUserEnv
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # schnellerer Download in PowerShell 5.1
$CreosonUrl = "https://github.com/SimplifiedLogic/creoson/releases/download/v3.0.2/CreosonServerWithSetup-3.0.2-win64.zip"
$CreosonSha256 = "4645d276950709130e6c1476715627e87862ff8ed3adcd4a78c771e04ace5f70"
$ProjectDir = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $ProjectDir ".venv"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
# .bat-Dateien in der OEM-Codepage der Konsole schreiben (Umlaute in Pfaden, z. B. C:\Users\Jürgen)
$BatEncoding = [Text.Encoding]::GetEncoding([Globalization.CultureInfo]::CurrentCulture.TextInfo.OEMCodePage)

function Step([string]$Text) { Write-Host "`n==> $Text" -ForegroundColor Cyan }

Step "Python 3.10+ suchen"
$pyCmd = Get-Command py -ErrorAction SilentlyContinue
if ($pyCmd) { $pyExe = "py"; $pyArgs = @("-3") } else { $pyExe = "python"; $pyArgs = @() }
& $pyExe @pyArgs -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.10 oder neuer fehlt: https://www.python.org/downloads/ (bei der Installation 'Add python.exe to PATH' anhaken)." }

Step "Virtuelle Umgebung anlegen und creo-mcp installieren"
if (-not (Test-Path $VenvDir)) { & $pyExe @pyArgs -m venv $VenvDir }
$VenvPy = Join-Path $VenvDir "Scripts\python.exe"
& $VenvPy -m pip install --upgrade pip | Out-Null
& $VenvPy -m pip install -e "$ProjectDir[windows]"
if ($LASTEXITCODE -ne 0) { throw "pip install ist fehlgeschlagen." }

Step "Creo-Installation suchen"
$creo = Get-ChildItem "C:\Program Files\PTC", "C:\PTC" -Directory -Filter "Creo *" -ErrorAction SilentlyContinue |
  Where-Object { Test-Path (Join-Path $_.FullName "Parametric\bin\parametric.exe") } |
  Sort-Object Name | Select-Object -Last 1
$Templates = $null
if ($creo) {
  $Common = Join-Path $creo.FullName "Common Files"
  $MsgExe = Join-Path $Common "x86e_win64\obj\pro_comm_msg.exe"
  $Parametric = Join-Path $creo.FullName "Parametric\bin\parametric.exe"
  $Templates = Join-Path $Common "templates"
  Write-Host "Gefunden: $($creo.FullName)"
} else {
  Write-Warning "Keine Creo-Installation gefunden. Startskripte bitte später von Hand anpassen."
}

Step "CREOSON-Ordner anlegen und für andere Benutzer sperren"
if ($CreosonDir -match "\s") { throw "Der CREOSON-Ordner darf keine Leerzeichen enthalten (CREOSON startet Creo sonst nicht): $CreosonDir" }
$me = [Security.Principal.WindowsIdentity]::GetCurrent()
$adminSid = "S-1-5-32-544"
if (Test-Path $CreosonDir) {
  $owner = (Get-Acl $CreosonDir).GetOwner([Security.Principal.SecurityIdentifier]).Value
  if ($owner -ne $me.User.Value -and $owner -ne $adminSid) {
    throw "$CreosonDir gehört einem anderen Benutzer ($owner). Aus Sicherheitsgründen abgebrochen - bitte -CreosonDir mit einem eigenen Ordner angeben."
  }
} else {
  New-Item -ItemType Directory -Path $CreosonDir | Out-Null
}
# Vererbung entfernen: nur du, SYSTEM und Administratoren (SIDs, damit es auch auf deutschem Windows passt)
& icacls $CreosonDir /inheritance:r /grant:r "*$($me.User.Value):(OI)(CI)F" "*S-1-5-18:(OI)(CI)F" "*$($adminSid):(OI)(CI)F" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Rechte für $CreosonDir konnten nicht gesetzt werden (icacls)." }

if (-not $SkipCreoson) {
  Step "CREOSON 3.0.2 herunterladen und prüfen"
  $zip = Join-Path $env:TEMP "CreosonServerWithSetup-3.0.2-win64.zip"
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  Invoke-WebRequest -Uri $CreosonUrl -OutFile $zip -UseBasicParsing
  $hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
  if ($hash -ne $CreosonSha256) { throw "SHA256 von CREOSON stimmt nicht ($hash). Abbruch." }
  Expand-Archive -Path $zip -DestinationPath $CreosonDir -Force
  Write-Host "CREOSON entpackt nach $CreosonDir"
}

if ($creo -and (Test-Path $CreosonDir)) {
  Step "Startskripte schreiben"
  New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
  $setvars = Join-Path $CreosonDir "setvars.bat"
  # Immer neu schreiben - eine vorhandene (evtl. fremde) setvars.bat wird nicht übernommen.
  $content = "@echo off`r`nset ""PROE_COMMON=$Common""`r`nset ""PROE_ENV=x86e_win64""`r`nset ""JAVA_HOME=$CreosonDir\jre""`r`nset ""JSON_PORT=$Port""`r`n"
  [IO.File]::WriteAllText($setvars, $content, $BatEncoding)
  Write-Host "setvars.bat geschrieben (CREOSON-Start: $CreosonDir\creoson_run.bat)"
  $bat = "@echo off`r`nrem Startet Creo so, dass CREOSON sich verbinden kann (J-Link async)`r`nset ""PRO_COMM_MSG_EXE=$MsgExe""`r`ncd /d ""$WorkDir""`r`nstart """" ""$Parametric""`r`n"
  [IO.File]::WriteAllText((Join-Path $CreosonDir "nitro_proe_remote.bat"), $bat, $BatEncoding)
  Write-Host "nitro_proe_remote.bat geschrieben (Arbeitsverzeichnis: $WorkDir)"
  if (-not $NoUserEnv) {
    [Environment]::SetEnvironmentVariable("PRO_COMM_MSG_EXE", $MsgExe, "User")
    Write-Host "PRO_COMM_MSG_EXE dauerhaft gesetzt - auch ein normal gestartetes Creo ist nach Neuanmeldung erreichbar."
  }
}

$envBlock = [ordered]@{
  CREOSON_URL = "http://localhost:$Port/creoson"
  CREO_VERSION = "12"
  CREO_START_DIR = $CreosonDir
}
if ($Templates) { $envBlock["CREO_TEMPLATE_DIR"] = $Templates }
$serverEntry = [ordered]@{ command = $VenvPy; args = @("-m", "creo_mcp"); env = $envBlock }

if (-not $SkipClaudeConfig) {
  Step "Claude Desktop konfigurieren"
  $cfgPath = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
  $cfg = $null
  if (Test-Path $cfgPath) {
    Copy-Item $cfgPath "$cfgPath.bak" -Force
    $raw = Get-Content $cfgPath -Raw
    if ($raw -and $raw.Trim()) { $cfg = $raw | ConvertFrom-Json }
  } else {
    New-Item -ItemType Directory -Force -Path (Split-Path $cfgPath) | Out-Null
  }
  if (-not $cfg) { $cfg = New-Object PSObject }
  if (-not $cfg.PSObject.Properties["mcpServers"]) { $cfg | Add-Member -NotePropertyName mcpServers -NotePropertyValue (New-Object PSObject) }
  $cfg.mcpServers | Add-Member -NotePropertyName creo -NotePropertyValue ([pscustomobject]$serverEntry) -Force
  [IO.File]::WriteAllText($cfgPath, ($cfg | ConvertTo-Json -Depth 20), $Utf8NoBom)
  Write-Host "Eingetragen in $cfgPath (Sicherung: .bak)"
}

Step "Netzwerkschutz: CREOSON hat kein Passwort und lauscht auf allen Netzwerkadressen"
$fwName = "CREOSON Port $Port nur lokal"
$isAdmin = ([Security.Principal.WindowsPrincipal]$me).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
  if (-not (Get-NetFirewallRule -DisplayName $fwName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $fwName -Direction Inbound -Protocol TCP -LocalPort $Port -Action Block | Out-Null
  }
  Write-Host "Firewall-Regel '$fwName' aktiv: andere Rechner im Netz erreichen CREOSON nicht (localhost bleibt erlaubt)."
} else {
  Write-Warning "Ohne Administratorrechte keine Firewall-Regel gesetzt. Wenn Windows beim ersten CREOSON-Start nach Netzwerkzugriff fragt: NICHT zulassen (Abbrechen). Oder als Administrator ausführen:"
  Write-Host "  New-NetFirewallRule -DisplayName '$fwName' -Direction Inbound -Protocol TCP -LocalPort $Port -Action Block"
}

Step "VB API registrieren (optional, für Eltern/Kind-Beziehungen der KEs)"
$vbReg = if ($creo) { Join-Path $creo.FullName "Parametric\bin\vb_api_register.bat" } else { $null }
if ($vbReg -and (Test-Path $vbReg) -and $isAdmin) {
  & cmd.exe /c "`"$vbReg`""
  if ($LASTEXITCODE -eq 0) { Write-Host "VB API registriert." } else { Write-Warning "vb_api_register.bat meldete Fehler $LASTEXITCODE - creo_feature_relations ist dann nicht verfügbar." }
} elseif ($vbReg -and (Test-Path $vbReg)) {
  Write-Host "Für die VB API dieses Skript als Administrator ausführen (oder einmal '$vbReg' als Administrator starten)."
} else {
  Write-Host "vb_api_register.bat nicht gefunden - VB API wird übersprungen (alle anderen Werkzeuge funktionieren)."
}

Step "Fertig - nächste Schritte"
Write-Host "1. CREOSON starten:   $CreosonDir\creoson_run.bat   (Fenster offen lassen)"
Write-Host "2. Creo starten:      $CreosonDir\nitro_proe_remote.bat"
Write-Host "3. Prüfen:            & '$VenvPy' -m creo_mcp doctor"
Write-Host "4. Claude Desktop komplett beenden (Tray) und neu starten. Dann fragen: 'Zeig mir den Modellbaum des aktiven Modells.'"
Write-Host "   Claude Code:  claude mcp add creo --scope user -e CREOSON_URL=http://localhost:$Port/creoson -e CREO_VERSION=12 -- `"$VenvPy`" -m creo_mcp"
