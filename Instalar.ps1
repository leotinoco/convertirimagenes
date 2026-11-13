<#
.SYNOPSIS
    Instalador de un solo clic de ConvertirImagenes para Windows.

.DESCRIPTION
    Lo lanza Instalar.bat. Pasos:
      1. Busca un Python 3.10+ con tkinter (py launcher, PATH, rutas habituales).
      2. Si no hay, descarga el instalador oficial de python.org, comprueba su
         firma digital y lo instala solo para este usuario, en silencio, sin
         tocar el PATH ni otros Python ya instalados (no pide administrador).
      3. Crea un entorno virtual propio y aislado, e instala ahi requirements.txt.
         El Python del sistema nunca se modifica.
      4. Crea un acceso directo en el Escritorio que apunta al Python de ese
         entorno (no depende del PATH).
      5. Abre la aplicacion.
    Es idempotente: cada paso se omite si ya esta hecho.

    Todo el texto es ASCII a proposito: Windows PowerShell 5.1 lee los .ps1 sin
    BOM como ANSI y la consola cmd mostraria mal los acentos.

.PARAMETER DirDatos
    Donde se guarda el entorno virtual. Por defecto %LOCALAPPDATA%\ConvertirImagenes.
.PARAMETER DirEscritorio
    Donde se crea el acceso directo. Por defecto, el Escritorio del usuario.
.PARAMETER SinAbrir
    No abre la aplicacion al terminar (para pruebas).
.PARAMETER ProbarDescarga
    Prueba: finge que no hay Python, descarga y verifica el instalador oficial,
    pero NO lo ejecuta ni cambia nada mas.
#>
[CmdletBinding()]
param(
    [string]$DirDatos = (Join-Path $env:LOCALAPPDATA 'ConvertirImagenes'),
    [string]$DirEscritorio = [Environment]::GetFolderPath('Desktop'),
    [switch]$SinAbrir,
    [switch]$ProbarDescarga
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # Invoke-WebRequest es muy lento con la barra
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch {}

$MinMayor = 3; $MinMenor = 10
# Se instala 3.13 (probado) y no la ultima: asi hay wheels de todas las dependencias.
# Se prueban en orden por si python.org retira alguno (las ultimas 3.13.x solo traen codigo fuente).
$VersionesPython = @('3.13.17', '3.13.16', '3.13.15')
$NombreAcceso = 'Convertir Imagenes.lnk'

$DirApp   = $PSScriptRoot
$Venv     = Join-Path $DirDatos 'venv'
$VenvPy   = Join-Path $Venv 'Scripts\python.exe'
$VenvPyw  = Join-Path $Venv 'Scripts\pythonw.exe'
$Reqs     = Join-Path $DirApp 'requirements.txt'
$AppPy    = Join-Path $DirApp 'app.py'

function Titulo($t) { Write-Host ''; Write-Host "== $t" -ForegroundColor Cyan }
function Ok($t)     { Write-Host "   [OK] $t" -ForegroundColor Green }
function Info($t)   { Write-Host "   $t" }
function Aviso($t)  { Write-Host "   [!] $t" -ForegroundColor Yellow }

class FalloInstalacion : System.Exception {
    FalloInstalacion([string]$m) : base($m) {}
}
function Fallar($m) { throw [FalloInstalacion]::new($m) }

# Ejecuta un exe y devuelve su salida; nunca lanza por un codigo de salida != 0.
function Ejecutar([string]$exe, [string[]]$args_) {
    $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $out = & $exe @args_ 2>&1 | Out-String; return @{ Codigo = $LASTEXITCODE; Salida = $out.Trim() } }
    catch { return @{ Codigo = -1; Salida = "$_" } }
    finally { $ErrorActionPreference = $prev }
}

# Devuelve la version "3.x.y" si $exe es un Python utilizable (>= 3.10, con tkinter y venv), o $null.
# Se rechazan los Python que viven dentro de un venv ajeno (se romperian al borrarlo), salvo el nuestro.
function Probar-Python([string]$exe, [bool]$permitirVenv = $false) {
    $EsVenv = if ($permitirVenv) { 'True' } else { 'False' }
    if (-not $exe -or -not (Test-Path -LiteralPath $exe)) { return $null }
    # El alias de la Microsoft Store (WindowsApps\python.exe) no es un Python real.
    if ($exe -like '*\WindowsApps\*') { return $null }
    $codigo = "import sys, tkinter, venv, ensurepip; " +
              "ok = sys.version_info >= ($MinMayor, $MinMenor); " +
              "ok = ok and (sys.prefix == sys.base_prefix or $EsVenv); " +
              "print(('OK ' if ok else 'VIEJO ') + '.'.join(map(str, sys.version_info[:3])))"
    $r = Ejecutar $exe @('-I', '-c', $codigo)
    if ($r.Codigo -eq 0 -and $r.Salida -match '^OK (\d+\.\d+\.\d+)$') { return $Matches[1] }
    return $null
}

# Reune candidatos: py launcher, PATH y carpetas de instalacion habituales; devuelve el de version mas alta.
function Buscar-Python {
    $candidatos = New-Object System.Collections.Generic.List[string]

    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        $r = Ejecutar $py.Source @('-0p')
        foreach ($linea in ($r.Salida -split "`r?`n")) {
            if ($linea -match '([A-Za-z]:\\.*?python\.exe)\s*$') { $candidatos.Add($Matches[1]) }
        }
    }
    foreach ($c in (Get-Command python.exe -All -ErrorAction SilentlyContinue)) { $candidatos.Add($c.Source) }

    $bases = @((Join-Path $env:LOCALAPPDATA 'Programs\Python'), $env:ProgramFiles, ${env:ProgramFiles(x86)}) | Where-Object { $_ }
    foreach ($b in $bases) {
        if (Test-Path $b) {
            Get-ChildItem -Path $b -Directory -Filter 'Python3*' -ErrorAction SilentlyContinue |
                ForEach-Object { $candidatos.Add((Join-Path $_.FullName 'python.exe')) }
        }
    }

    $mejor = $null; $vistos = @{}
    foreach ($c in $candidatos) {
        $clave = $c.ToLowerInvariant()
        if ($vistos.ContainsKey($clave)) { continue }
        $vistos[$clave] = $true
        $v = Probar-Python $c
        if ($v -and (-not $mejor -or [version]$v -gt [version]$mejor.Version)) {
            $mejor = @{ Exe = $c; Version = $v }
        }
    }
    return $mejor
}

function Instalar-Python([bool]$soloProbar) {
    $arq = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
    $sufijo = switch ($arq) { 'AMD64' { 'amd64' } 'ARM64' { 'arm64' } default { Fallar "Arquitectura no soportada ($arq). Hace falta Windows de 64 bits." } }

    $tmp = Join-Path ([IO.Path]::GetTempPath()) ('ConvertirImagenes-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Path $tmp | Out-Null
    try {
        $instalador = $null
        foreach ($v in $VersionesPython) {
            $url = "https://www.python.org/ftp/python/$v/python-$v-$sufijo.exe"
            $dest = Join-Path $tmp "python-$v-$sufijo.exe"
            Info "Descargando Python $v desde python.org (unos 25 MB)..."
            try { Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing; $instalador = $dest; $verElegida = $v; break }
            catch { Aviso "No se pudo descargar Python $v ($($_.Exception.Message)). Probando otra version..." }
        }
        if (-not $instalador) { Fallar 'No se pudo descargar Python. Revisa tu conexion a Internet y vuelve a ejecutar Instalar.bat.' }

        # Solo se ejecuta si lo firma la Python Software Foundation.
        $firma = Get-AuthenticodeSignature -LiteralPath $instalador
        if ($firma.Status -ne 'Valid' -or $firma.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
            Fallar "El instalador descargado no tiene una firma valida de la Python Software Foundation (estado: $($firma.Status)). No se ejecutara."
        }
        Ok "Descarga verificada (firma de la Python Software Foundation)."

        if ($soloProbar) { Info 'Modo prueba: no se ejecuta el instalador.'; return $null }

        Info "Instalando Python $verElegida solo para tu usuario (1-3 minutos, no cierres la ventana)..."
        # Per-usuario: sin administrador, sin PATH, sin py launcher, sin tocar otros Python.
        $r = Start-Process -FilePath $instalador -Wait -PassThru -ArgumentList @(
            '/quiet', 'InstallAllUsers=0', 'PrependPath=0', 'Include_launcher=0', 'Include_test=0',
            'Include_doc=0', 'Include_tcltk=1', 'Include_pip=1', 'Shortcuts=0', 'AssociateFiles=0')
        if ($r.ExitCode -ne 0) { Fallar "El instalador de Python termino con el codigo $($r.ExitCode)." }
        Ok "Python $verElegida instalado."
    }
    finally { Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue }

    $p = Buscar-Python
    if (-not $p) { Fallar 'Python se instalo pero no se pudo localizar. Reinicia el equipo y vuelve a ejecutar Instalar.bat.' }
    return $p
}

# El entorno es valido si su python funciona, y su Python base sigue existiendo.
function Venv-Sano { return [bool](Probar-Python $VenvPy $true) }

function Dependencias-Ok {
    $r = Ejecutar $VenvPy @('-I', '-c', 'import customtkinter, PIL, piexif, darkdetect, dotenv, tkinterdnd2')
    return ($r.Codigo -eq 0)
}

function Crear-Acceso {
    New-Item -ItemType Directory -Force -Path $DirEscritorio | Out-Null
    $ruta = Join-Path $DirEscritorio $NombreAcceso
    $ws = New-Object -ComObject WScript.Shell
    $a = $ws.CreateShortcut($ruta)
    $a.TargetPath       = $VenvPyw
    $a.Arguments        = '"' + $AppPy + '"'
    $a.WorkingDirectory = $DirApp
    $a.Description      = 'Conversor masivo de imagenes (AVIF, WebP, JPG, PNG)'
    $a.IconLocation     = "$VenvPyw,0"
    $a.Save()
    return $ruta
}

# ---------------------------------------------------------------------------
$codigoSalida = 0
try {
    Write-Host ''
    Write-Host '  ============================================' -ForegroundColor Cyan
    Write-Host '    Instalador de ConvertirImagenes' -ForegroundColor Cyan
    Write-Host '  ============================================' -ForegroundColor Cyan
    Write-Host '  Esto puede tardar unos minutos la primera vez.'
    Write-Host '  No hace falta ser administrador ni saber de Python.'

    if (-not (Test-Path -LiteralPath $AppPy)) { Fallar "No encuentro app.py en $DirApp. Descomprime TODA la carpeta del programa antes de instalar." }
    if (-not (Test-Path -LiteralPath $Reqs))  { Fallar "No encuentro requirements.txt en $DirApp." }

    # --- 1. Python ---------------------------------------------------------
    Titulo 'Paso 1 de 4: buscando Python 3.10 o superior'
    $python = $null
    if ($ProbarDescarga) {
        Aviso 'Modo prueba: se finge que no hay Python.'
        Instalar-Python $true | Out-Null
        Write-Host ''; Ok 'Prueba de descarga terminada. No se cambio nada.'
        return
    }
    $yaListo = Venv-Sano
    if ($yaListo) {
        Ok "Ya hay un entorno de la aplicacion listo (Python $(Probar-Python $VenvPy $true)). Se reutiliza."
        Titulo 'Paso 2 de 4: preparando el entorno de la aplicacion'
        Ok 'Entorno ya existente, no hace falta crearlo.'
    }
    else {
        $python = Buscar-Python
        if ($python) { Ok "Python $($python.Version) encontrado: $($python.Exe)" }
        else {
            Info 'No hay un Python adecuado en este equipo. Se instalara automaticamente.'
            $python = Instalar-Python $false
            Ok "Usando Python $($python.Version): $($python.Exe)"
        }

        # --- 2. Entorno virtual -------------------------------------------
        Titulo 'Paso 2 de 4: preparando el entorno de la aplicacion'
        if (Test-Path -LiteralPath $Venv) {
            Aviso 'El entorno anterior estaba danado o apunta a un Python que ya no existe; se recrea.'
            Remove-Item -LiteralPath $Venv -Recurse -Force
        }
        New-Item -ItemType Directory -Force -Path $DirDatos | Out-Null
        $r = Ejecutar $python.Exe @('-m', 'venv', $Venv)
        if ($r.Codigo -ne 0 -or -not (Test-Path -LiteralPath $VenvPy)) { Fallar "No se pudo crear el entorno:`n$($r.Salida)" }
        Ok "Entorno creado en $Venv"
    }

    # --- 3. Dependencias ---------------------------------------------------
    Titulo 'Paso 3 de 4: instalando las dependencias'
    if (Dependencias-Ok) { Ok 'Las dependencias ya estaban instaladas.' }
    else {
        Info 'Descargando paquetes (customtkinter, Pillow, ...). Puede tardar un poco.'
        & $VenvPy -I -m pip install --disable-pip-version-check --upgrade -r $Reqs
        if ($LASTEXITCODE -ne 0) { Fallar 'No se pudieron instalar las dependencias (ver el error de arriba). Comprueba tu conexion a Internet y vuelve a ejecutar Instalar.bat.' }
        if (-not (Dependencias-Ok)) { Fallar 'Las dependencias se instalaron pero no se pueden importar.' }
        Ok 'Dependencias instaladas.'
    }

    # --- 4. Acceso directo -------------------------------------------------
    Titulo 'Paso 4 de 4: creando el acceso directo en el Escritorio'
    $lnk = Crear-Acceso
    Ok "Acceso directo: $lnk"

    Write-Host ''
    Write-Host '  ============================================' -ForegroundColor Green
    Write-Host '    Instalacion completada' -ForegroundColor Green
    Write-Host '  ============================================' -ForegroundColor Green
    Write-Host '  A partir de ahora abre la app con el icono "Convertir Imagenes" del Escritorio.'
    if (-not $SinAbrir) {
        Info 'Abriendo la aplicacion...'
        Start-Process -FilePath $VenvPyw -ArgumentList ('"' + $AppPy + '"') -WorkingDirectory $DirApp
    }
}
catch {
    $codigoSalida = 1
    Write-Host ''
    Write-Host '  ============================================' -ForegroundColor Red
    Write-Host '    La instalacion no se pudo completar' -ForegroundColor Red
    Write-Host '  ============================================' -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception -isnot [FalloInstalacion]) { Write-Host "  ($($_.InvocationInfo.PositionMessage))" -ForegroundColor DarkGray }
    Write-Host ''
    Write-Host '  Puedes volver a ejecutar Instalar.bat: retoma lo que falte.'
}
exit $codigoSalida
