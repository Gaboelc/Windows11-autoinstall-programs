import subprocess
import sys
import shutil
from dataclasses import dataclass

# Found the ID in: https://winget.run  or execute: winget search <name>
WINGET_APPS = [

    # Gaming
    "Valve.Steam",
    "EpicGames.EpicGamesLauncher",
    "ElectronicArts.EADesktop",
    "GOG.Galaxy",
    "Overwolf.CurseForge",
    "Nvidia.GeForceExperience",

    # Development
    "Git.Git",
    "Microsoft.VisualStudioCode",
    "Notepad++.Notepad++",
    "Docker.DockerDesktop",
    "Anaconda.Miniconda3",
    "Microsoft.WindowsTerminal",

    # Communication & Social
    "Discord.Discord",
    "Spotify.Spotify",

    # Productivity & Utilities
    "7zip.7zip",
    "CodeSector.TeraCopy",
    "Foxit.FoxitReader",
    "Google.Drive",
    "NordVPN.NordVPN",

    # Creative & Media
    "GIMP.GIMP",
    "OBSProject.OBSStudio",
    "Microsoft.PowerBI",

    # Hardware & Peripherals
    "Logitech.OptionsPlus",

]

PIP_PACKAGES = [

    # HTTP & Web Scraping
    "requests",
    "beautifulsoup4",

    # Data & Analysis
    "numpy",
    "pandas",
    "scipy",

    # Machine Learning
    "scikit-learn",

    # Visualization
    "matplotlib",
    "seaborn",
    "plotly",

]

class Color:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    BLUE   = "\033[94m"


@dataclass
class Result:
    name: str
    status: str
    detail: str = ""


def header(text: str) -> None:
    print(f"\n{Color.BOLD}{Color.BLUE}{'─' * 60}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}  {text}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{'─' * 60}{Color.RESET}\n")


def log(symbol: str, color: str, name: str, msg: str) -> None:
    print(f"  {color}{symbol}{Color.RESET}  {Color.BOLD}{name}{Color.RESET} — {msg}")


def run(cmd: list[str]) -> tuple[int, str]:
    """Ejecuta un comando y devuelve (código de salida, salida combinada)."""
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout.strip()


# ── WINGET ────────────────────────────────────────────────────────────────────

def check_winget() -> bool:
    return shutil.which("winget") is not None


def install_winget_app(app_id: str) -> Result:
    """Intenta actualizar; si no está instalado, lo instala."""
    code, out = run([
        "winget", "upgrade", "--id", app_id,
        "--silent", "--accept-source-agreements", "--accept-package-agreements",
    ])

    if code == 0:
        if "No applicable upgrade found" in out or "No se encontró ninguna actualización" in out:
            return Result(app_id, "sin cambios", "Ya está en la última versión")
        return Result(app_id, "actualizado", "Actualizado correctamente")

    code2, out2 = run([
        "winget", "install", "--id", app_id,
        "--silent", "--accept-source-agreements", "--accept-package-agreements",
    ])

    if code2 == 0:
        return Result(app_id, "instalado", "Instalado correctamente")

    if "already installed" in out2.lower() or "ya está instalado" in out2.lower():
        return Result(app_id, "sin cambios", "Ya estaba instalado")

    return Result(app_id, "error", out2.splitlines()[-1] if out2 else "Error desconocido")


def process_winget(apps: list[str]) -> list[Result]:
    header("📦 Apps del sistema (winget)")
    results = []
    for app in apps:
        print(f"  ⏳ Procesando {Color.BOLD}{app}{Color.RESET}...")
        r = install_winget_app(app)
        results.append(r)
        _log_result(r)
    return results


# ── PIP ───────────────────────────────────────────────────────────────────────

def install_pip_package(pkg: str) -> Result:
    code, out = run([sys.executable, "-m", "pip", "install", "--upgrade", pkg])
    if code != 0:
        return Result(pkg, "error", out.splitlines()[-1] if out else "Error desconocido")

    if f"Successfully installed {pkg}" in out or "Installing" in out:
        if "Requirement already satisfied" in out:
            return Result(pkg, "sin cambios", "Ya estaba en la última versión")
        return Result(pkg, "actualizado" if "Upgrading" in out else "instalado", "OK")
    return Result(pkg, "sin cambios", "Ya estaba en la última versión")


def process_pip(packages: list[str]) -> list[Result]:
    header("🐍 Paquetes de Python (pip)")
    results = []
    for pkg in packages:
        print(f"  ⏳ Procesando {Color.BOLD}{pkg}{Color.RESET}...")
        r = install_pip_package(pkg)
        results.append(r)
        _log_result(r)
    return results



# ── HELPERS ───────────────────────────────────────────────────────────────────

def _log_result(r: Result) -> None:
    match r.status:
        case "instalado":
            log("✔", Color.GREEN, r.name, f"Instalado  {r.detail}")
        case "actualizado":
            log("↑", Color.CYAN, r.name, f"Actualizado  {r.detail}")
        case "sin cambios":
            log("•", Color.YELLOW, r.name, r.detail)
        case "omitido":
            log("⊘", Color.YELLOW, r.name, r.detail)
        case "error":
            log("✘", Color.RED, r.name, f"Error: {r.detail}")


def print_summary(all_results: list[Result]) -> None:
    header("📊 Resumen")
    counts = {"instalado": 0, "actualizado": 0, "sin cambios": 0, "omitido": 0, "error": 0}
    errors = []

    for r in all_results:
        counts[r.status] = counts.get(r.status, 0) + 1
        if r.status == "error":
            errors.append(r)

    total = len(all_results)
    print(f"  Total procesados : {Color.BOLD}{total}{Color.RESET}")
    print(f"  {Color.GREEN}✔ Instalados     : {counts['instalado']}{Color.RESET}")
    print(f"  {Color.CYAN}↑ Actualizados   : {counts['actualizado']}{Color.RESET}")
    print(f"  {Color.YELLOW}• Sin cambios    : {counts['sin cambios']}{Color.RESET}")
    print(f"  {Color.YELLOW}⊘ Omitidos       : {counts['omitido']}{Color.RESET}")
    print(f"  {Color.RED}✘ Errores        : {counts['error']}{Color.RESET}")

    if errors:
        print(f"\n  {Color.RED}{Color.BOLD}Elementos con error:{Color.RESET}")
        for r in errors:
            print(f"    • {r.name}: {r.detail}")

    print()


def main() -> None:
    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 60}")
    print("  🚀  INSTALADOR AUTOMÁTICO DE WINDOWS")
    print(f"{'═' * 60}{Color.RESET}")

    all_results: list[Result] = []

    # --- Winget ---
    if WINGET_APPS:
        if check_winget():
            all_results += process_winget(WINGET_APPS)
        else:
            print(f"\n  {Color.RED}✘ winget no encontrado.{Color.RESET} Instalalo desde: https://aka.ms/winget\n")
            all_results += [Result(a, "omitido", "winget no disponible") for a in WINGET_APPS]

    # --- Pip ---
    if PIP_PACKAGES:
        all_results += process_pip(PIP_PACKAGES)

    print_summary(all_results)


if __name__ == "__main__":
    main()