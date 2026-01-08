#!/usr/bin/env python3
"""
Git Sync Script für das Model_3_Backtest-Repository
Führt git pull und push mit Sicherheitsabfragen durch.

Repository: Carv1n/Model_3_Backtest

Features:
- Normal Pull/Push mit Konfliktprüfung
- Force Pull: Überschreibt ALLE lokalen Änderungen mit Remote
- Force Push: Überschreibt ALLES auf Remote mit lokalem Stand
- Verifikation mit Yes/No Bestätigung vor Force-Operationen
"""

import subprocess
import sys
import os
from pathlib import Path

# Projektverzeichnis
PROJECT_DIR = Path(__file__).parent.absolute()

def run_command(cmd, cwd=None):
    """Führt einen Shell-Befehl aus und gibt das Ergebnis zurück."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or PROJECT_DIR,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def auto_commit_changes():
    """Committed automatisch alle uncommitted Änderungen."""
    from datetime import datetime

    success, stdout, stderr = run_command("git status --porcelain")

    if not stdout.strip():
        print("✅ Keine uncommitted Änderungen.")
        return True

    print("\n📝 Auto-Commit: Folgende Änderungen werden committed:")
    print("-" * 60)
    # Zeige alle uncommitted Dateien
    lines = stdout.strip().split('\n')
    for line in lines[:20]:  # Erste 20 Dateien
        print(f"  {line}")
    if len(lines) > 20:
        print(f"  ... und {len(lines) - 20} weitere Dateien")
    print("-" * 60)

    # Auto-Commit mit Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Auto-commit via git_sync.py - {timestamp}"

    run_command("git add .")
    success, stdout, stderr = run_command(f'git commit -m "{message}"')

    if success:
        print(f"✅ Auto-Commit erfolgreich!")
        return True
    else:
        print(f"❌ Auto-Commit fehlgeschlagen: {stderr}")
        return False

def confirm_action(action_name):
    """Fragt User mit yes/no ob Aktion ausgeführt werden soll."""
    while True:
        response = input(f"\n⚠️  {action_name} ausführen? (yes/no): ").strip().lower()
        if response == "yes":
            return True
        elif response == "no":
            print("❌ Abgebrochen.")
            return False
        else:
            print("❌ Ungültige Eingabe! Bitte 'yes' oder 'no' eingeben.")

def check_git_status():
    """Prüft den Git-Status und zeigt lokale Änderungen."""
    print("=" * 60)
    print("📊 Git Status prüfen...")
    print("=" * 60)

    success, stdout, stderr = run_command("git status")
    if not success:
        print(f"❌ Fehler beim Git-Status: {stderr}")
        return False

    print(stdout)

    # Prüfe ob es lokale Änderungen gibt
    if "Changes not staged" in stdout or "Changes to be committed" in stdout or "Untracked files" in stdout:
        return True
    return False

def git_pull():
    """Führt git pull aus mit Auto-Commit."""
    print("\n" + "=" * 60)
    print("⬇️  Git Pull Vorbereitung...")
    print("=" * 60)

    # Auto-Commit lokaler Änderungen
    if not auto_commit_changes():
        return False

    # Zeige was vom Remote geholt wird
    success, branch, _ = run_command("git branch --show-current")
    branch = branch.strip() if success else "main"

    run_command("git fetch origin")
    success, stdout, stderr = run_command(f"git log HEAD..origin/{branch} --oneline")
    if success and stdout.strip():
        print(f"\n📥 Folgendes wird vom Remote geholt (origin/{branch}):")
        print("-" * 60)
        print(stdout[:500])
        print("-" * 60)
    else:
        print("\n✅ Keine neuen Änderungen auf Remote.")

    # Bestätigung
    if not confirm_action("Git Pull"):
        return False

    # Pull ausführen
    print("\n⬇️  Führe Git Pull aus...")
    success, stdout, stderr = run_command("git pull")

    if success:
        print("✅ Git Pull erfolgreich!")
        if stdout.strip():
            print(stdout)
        return True
    else:
        print("❌ Git Pull fehlgeschlagen!")
        print(f"Fehler: {stderr}")
        return False

def check_large_files():
    """Prüft auf Dateien >100MB (GitHub Limit) - Windows/macOS/Linux kompatibel."""
    print("\n" + "=" * 60)
    print("🔍 Prüfe auf Dateien >100 MB (GitHub-Limit)...")
    print("=" * 60)

    large_files = []

    try:
        # Durchsuche alle Dateien mit Python (plattformunabhängig)
        for root, dirs, files in os.walk(PROJECT_DIR):
            # Überspringe .git Ordner
            if '.git' in root:
                continue

            for file in files:
                file_path = Path(root) / file
                try:
                    size_bytes = file_path.stat().st_size
                    size_mb = size_bytes / (1024 * 1024)

                    if size_mb > 100:
                        rel_path = file_path.relative_to(PROJECT_DIR)
                        large_files.append((str(rel_path), size_mb))
                except (PermissionError, OSError):
                    continue

        if large_files:
            print(f"\n⚠️  WARNUNG: {len(large_files)} Datei(en) >100 MB gefunden:")
            print("=" * 60)
            for file_path, size_mb in large_files:
                print(f"  📁 {file_path} ({size_mb:.1f} MB)")
            print("=" * 60)
            print("\n💡 Diese Dateien können NICHT zu GitHub gepusht werden!")
            print("   Füge sie zur .gitignore hinzu falls sie nicht gepusht werden sollen.")
        else:
            print("✅ Keine Dateien >100 MB - ALLES kann gepusht werden!")

    except Exception as e:
        print(f"⚠️  Fehler beim Prüfen: {e}")

    return large_files

def git_push():
    """Führt git push aus mit Auto-Commit."""
    print("\n" + "=" * 60)
    print("⬆️  Git Push Vorbereitung...")
    print("=" * 60)

    # Auto-Commit lokaler Änderungen
    if not auto_commit_changes():
        return False

    # Prüfe auf zu große Dateien VOR dem Push
    large_files = check_large_files()

    # Zeige was gepusht wird
    success, branch, _ = run_command("git branch --show-current")
    branch = branch.strip() if success else "main"

    success, stdout, stderr = run_command(f"git log origin/{branch}..HEAD --oneline")
    if success and stdout.strip():
        print(f"\n📤 Folgendes wird zu Remote gepusht (origin/{branch}):")
        print("-" * 60)
        print(stdout[:500])
        print("-" * 60)
    else:
        print("\n✅ Keine neuen lokalen Commits zum Pushen.")

    # Bestätigung
    if not confirm_action("Git Push"):
        return False

    # Push ausführen
    print("\n⬆️  Führe Git Push aus...")
    success, stdout, stderr = run_command("git push")

    if success:
        print("✅ Git Push erfolgreich!")
        if stdout.strip():
            print(stdout)

        # Zeige Zusammenfassung
        if large_files:
            print(f"\n⚠️  Hinweis: {len(large_files)} Datei(en) >100MB konnten nicht gepusht werden")
        else:
            print("\n✅ ALLE Dateien erfolgreich gepusht!")

        return True
    else:
        print("❌ Git Push fehlgeschlagen!")
        print(f"Fehler: {stderr}")

        if "no upstream branch" in stderr:
            print("\n💡 Tipp: Erstelle einen upstream branch mit:")
            print("   git push -u origin main")

        # Zeige Hinweis auf große Dateien falls vorhanden
        if large_files and ("too large" in stderr.lower() or "size exceeds" in stderr.lower()):
            print("\n⚠️  Große Dateien gefunden (siehe oben)!")
            print("   Lösung: Füge sie zur .gitignore hinzu:")
            for file_path, _ in large_files:
                print(f"     echo '{file_path}' >> .gitignore")

        return False

def git_force_pull():
    """Führt Force Pull aus - überschreibt ALLE lokalen Änderungen mit Remote."""
    print("\n" + "=" * 60)
    print("⚠️  FORCE PULL - Alle lokalen Änderungen werden überschrieben!")
    print("=" * 60)

    # Zeige was überschrieben wird
    success, stdout, stderr = run_command("git status")
    if success:
        print("\n📋 Aktueller Status (wird überschrieben):")
        print(stdout)

    # Hole Remote-Informationen
    success, stdout, stderr = run_command("git fetch origin")
    if not success:
        print(f"❌ Fehler beim Fetch: {stderr}")
        return False

    # Zeige was vom Remote kommt
    success, branch, _ = run_command("git branch --show-current")
    branch = branch.strip() if success else "main"

    success, stdout, stderr = run_command(f"git log HEAD..origin/{branch} --oneline")
    if success and stdout.strip():
        print(f"\n📥 Wird vom Remote geholt (origin/{branch}):")
        print(stdout[:500])  # Erste 500 Zeichen

    # Verifikation
    print("\n" + "=" * 60)
    print("⚠️  WARNUNG: Force Pull wird folgendes tun:")
    print("=" * 60)
    print("  ❌ ALLE lokalen Änderungen werden VERWORFEN")
    print("  ❌ ALLE uncommitted Dateien werden überschrieben")
    print("  ✅ Lokales Repository wird identisch mit Remote")
    print("  ✅ Befehl: git reset --hard origin/" + branch)
    print("=" * 60)

    # Bestätigung
    if not confirm_action("⚠️  FORCE PULL"):
        return False

    # Führe Force Pull aus
    print("\n🔄 Führe Force Pull aus...")
    success, stdout, stderr = run_command(f"git reset --hard origin/{branch}")

    if success:
        print("✅ Force Pull erfolgreich!")
        print("📁 Lokales Repository ist jetzt identisch mit Remote.")
        if stdout.strip():
            print(stdout)
        return True
    else:
        print("❌ Force Pull fehlgeschlagen!")
        print(f"Fehler: {stderr}")
        return False

def git_force_push():
    """Führt Force Push aus - überschreibt ALLES auf Remote mit lokal."""
    print("\n" + "=" * 60)
    print("⚠️  FORCE PUSH - Remote wird mit lokalem Stand überschrieben!")
    print("=" * 60)

    # Auto-Commit lokaler Änderungen
    if not auto_commit_changes():
        return False

    # Zeige lokalen Status
    success, stdout, stderr = run_command("git status")
    if success:
        print("\n📋 Lokaler Stand (wird zu Remote gepusht):")
        print(stdout)

    # Zeige was überschrieben wird
    success, branch, _ = run_command("git branch --show-current")
    branch = branch.strip() if success else "main"

    success, stdout, stderr = run_command(f"git log origin/{branch}..HEAD --oneline")
    if success and stdout.strip():
        print(f"\n📤 Wird zu Remote gepusht (origin/{branch}):")
        print(stdout[:500])

    # Verifikation
    print("\n" + "=" * 60)
    print("⚠️  WARNUNG: Force Push wird folgendes tun:")
    print("=" * 60)
    print("  ❌ ALLE Remote-Änderungen werden ÜBERSCHRIEBEN")
    print("  ❌ Andere Entwickler könnten Probleme bekommen")
    print("  ✅ Remote wird identisch mit lokalem Stand")
    print("  ✅ Befehl: git push --force origin " + branch)
    print("=" * 60)

    # Bestätigung
    if not confirm_action("⚠️  FORCE PUSH"):
        return False

    # Führe Force Push aus
    print("\n🔄 Führe Force Push aus...")
    success, stdout, stderr = run_command(f"git push --force origin {branch}")

    if success:
        print("✅ Force Push erfolgreich!")
        print("📁 Remote Repository ist jetzt identisch mit lokal.")
        if stdout.strip():
            print(stdout)
        return True
    else:
        print("❌ Force Push fehlgeschlagen!")
        print(f"Fehler: {stderr}")
        return False

def undo_last_operation():
    """Macht letzten Pull/Push rückgängig mit git reflog."""
    print("\n" + "=" * 60)
    print("↩️  Undo - Letzte Git-Operation rückgängig machen")
    print("=" * 60)

    # Zeige letzte Git-Operationen
    success, stdout, stderr = run_command("git reflog -10")
    if not success:
        print(f"❌ Fehler beim Abrufen von git reflog: {stderr}")
        return False

    print("\n📜 Letzte 10 Git-Operationen:")
    print("-" * 60)
    print(stdout)
    print("-" * 60)

    print("\n💡 Um zum vorherigen Stand zurückzukehren:")
    print("   Gib die Nummer ein (z.B. '1' für HEAD@{1})")
    print("   oder 'no' zum Abbrechen")

    response = input("\n⚠️  Zu welchem Stand zurück? (Nummer oder 'no'): ").strip().lower()

    if response == "no":
        print("❌ Abgebrochen.")
        return False

    # Prüfe ob Nummer
    try:
        step = int(response)
        if step < 0 or step > 9:
            print("❌ Ungültige Nummer! Bitte 0-9 eingeben.")
            return False
    except ValueError:
        print("❌ Ungültige Eingabe! Bitte eine Nummer oder 'no' eingeben.")
        return False

    # Zeige was dieser Stand war
    success, stdout, stderr = run_command(f"git show HEAD@{{{step}}} --stat")
    if success:
        print(f"\n📋 Stand HEAD@{{{step}}}:")
        print("-" * 60)
        print(stdout[:500])
        print("-" * 60)

    # Finale Bestätigung
    if not confirm_action(f"Reset zu HEAD@{{{step}}}"):
        return False

    # Führe Reset aus
    print(f"\n🔄 Führe Reset zu HEAD@{{{step}}} aus...")
    success, stdout, stderr = run_command(f"git reset --hard HEAD@{{{step}}}")

    if success:
        print("✅ Undo erfolgreich!")
        print(f"📁 Repository wurde zu HEAD@{{{step}}} zurückgesetzt.")
        if stdout.strip():
            print(stdout)
        return True
    else:
        print("❌ Undo fehlgeschlagen!")
        print(f"Fehler: {stderr}")
        return False

def main():
    """Hauptfunktion."""
    print("\n" + "=" * 60)
    print("🔄 Git Sync Script für Model_3_Backtest Repository")
    print("📦 Repository: Carv1n/Model_3_Backtest")
    print("=" * 60)
    print(f"📁 Projektverzeichnis: {PROJECT_DIR}")
    print()

    # Prüfe ob wir in einem Git-Repository sind
    success, _, stderr = run_command("git rev-parse --git-dir")
    if not success:
        print("❌ Fehler: Kein Git-Repository gefunden!")
        print("Bitte führe 'git init' aus oder navigiere in ein Git-Repository.")
        sys.exit(1)

    # Zeige aktuellen Branch
    success, branch, _ = run_command("git branch --show-current")
    if success:
        print(f"🌿 Aktueller Branch: {branch.strip()}")

    # Menü
    print("\nWas möchtest du tun?")
    print("  1. Git Pull (Änderungen vom Server holen)")
    print("  2. Git Push (Änderungen zum Server senden)")
    print("  3. Beides (Pull dann Push)")
    print("  4. ⚠️  FORCE Pull (überschreibt ALLE lokalen Änderungen)")
    print("  5. ⚠️  FORCE Push (überschreibt ALLES auf Remote)")
    print("  6. Nur Status anzeigen")
    print("  7. ↩️  Undo - Letzte Operation rückgängig machen")
    print("  8. Abbrechen")

    choice = input("\nWähle eine Option (1-8): ").strip()

    if choice == "1":
        # Git Pull
        check_git_status()
        git_pull()

    elif choice == "2":
        # Git Push
        check_git_status()
        git_push()

    elif choice == "3":
        # Pull dann Push
        check_git_status()
        if git_pull():
            print("\n" + "-" * 60)
            git_push()

    elif choice == "4":
        # Force Pull
        check_git_status()
        git_force_pull()

    elif choice == "5":
        # Force Push
        check_git_status()
        git_force_push()

    elif choice == "6":
        # Nur Status
        check_git_status()

    elif choice == "7":
        # Undo
        undo_last_operation()

    elif choice == "8":
        print("👋 Abgebrochen.")
        return

    else:
        print("❌ Ungültige Auswahl!")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Fertig!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer.")
        sys.exit(0)
