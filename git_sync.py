#!/usr/bin/env python3
"""
Git Sync Script für Model 3 Backtest Projekt
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
    if "Changes not staged" in stdout or "Changes to be committed" in stdout:
        return True
    return False

def git_pull():
    """Führt git pull aus."""
    print("\n" + "=" * 60)
    print("⬇️  Git Pull ausführen...")
    print("=" * 60)

    success, stdout, stderr = run_command("git pull")

    if success:
        print("✅ Git Pull erfolgreich!")
        if stdout.strip():
            print(stdout)
        return True
    else:
        print("❌ Git Pull fehlgeschlagen!")
        print(f"Fehler: {stderr}")

        if "Your local changes" in stderr or "would be overwritten" in stderr:
            print("\n⚠️  WICHTIG: Es gibt lokale Änderungen, die überschrieben würden!")
            print("Optionen:")
            print("  1. Änderungen stashen: git stash")
            print("  2. Änderungen committen: git add . && git commit -m 'Deine Nachricht'")
            print("  3. Änderungen verwerfen: git restore <datei>")

        return False

def git_push():
    """Führt git push aus."""
    print("\n" + "=" * 60)
    print("⬆️  Git Push ausführen...")
    print("=" * 60)

    # Prüfe ob es uncommitted Änderungen gibt
    success, stdout, stderr = run_command("git status --porcelain")
    if stdout.strip():
        print("⚠️  Es gibt uncommitted Änderungen!")
        print("Möchtest du diese Änderungen committen? (j/n): ", end="")
        response = input().strip().lower()

        if response == 'j':
            print("\n📝 Änderungen committen...")
            print("Commit-Nachricht eingeben: ", end="")
            message = input().strip()
            if not message:
                message = "Auto-commit via git_sync.py"

            # Add und Commit
            run_command("git add .")
            success, stdout, stderr = run_command(f'git commit -m "{message}"')
            if not success:
                print(f"❌ Commit fehlgeschlagen: {stderr}")
                return False
            print("✅ Änderungen committed!")
        else:
            print("⏭️  Push übersprungen (uncommitted Änderungen)")
            return False

    # Push ausführen
    success, stdout, stderr = run_command("git push")

    if success:
        print("✅ Git Push erfolgreich!")
        if stdout.strip():
            print(stdout)
        return True
    else:
        print("❌ Git Push fehlgeschlagen!")
        print(f"Fehler: {stderr}")

        if "no upstream branch" in stderr:
            print("\n💡 Tipp: Erstelle einen upstream branch mit:")
            print("   git push -u origin main")

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

    response = input("\n⚠️  Bist du sicher? (yes/no): ").strip().lower()
    if response != "yes":
        print("❌ Abgebrochen. Nichts wurde geändert.")
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

    # Prüfe ob es uncommitted Änderungen gibt
    success, stdout, stderr = run_command("git status --porcelain")
    if stdout.strip():
        print("\n⚠️  Es gibt uncommitted Änderungen!")
        print("Möchtest du diese Änderungen committen? (j/n): ", end="")
        response = input().strip().lower()

        if response == 'j':
            print("\n📝 Änderungen committen...")
            print("Commit-Nachricht eingeben: ", end="")
            message = input().strip()
            if not message:
                message = "Auto-commit via git_sync.py"

            # Add und Commit
            run_command("git add .")
            success, stdout, stderr = run_command(f'git commit -m "{message}"')
            if not success:
                print(f"❌ Commit fehlgeschlagen: {stderr}")
                return False
            print("✅ Änderungen committed!")
        else:
            print("⏭️  Force Push übersprungen (uncommitted Änderungen)")
            return False

    # Verifikation
    print("\n" + "=" * 60)
    print("⚠️  WARNUNG: Force Push wird folgendes tun:")
    print("=" * 60)
    print("  ❌ ALLE Remote-Änderungen werden ÜBERSCHRIEBEN")
    print("  ❌ Andere Entwickler könnten Probleme bekommen")
    print("  ✅ Remote wird identisch mit lokalem Stand")
    print("  ✅ Befehl: git push --force origin " + branch)
    print("=" * 60)

    response = input("\n⚠️  Bist du sicher? (yes/no): ").strip().lower()
    if response != "yes":
        print("❌ Abgebrochen. Nichts wurde geändert.")
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

def main():
    """Hauptfunktion."""
    print("\n" + "=" * 60)
    print("🔄 Git Sync Script für Model 3 Backtest")
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
    print("  7. Abbrechen")

    choice = input("\nWähle eine Option (1-7): ").strip()

    if choice == "1":
        # Prüfe Status zuerst
        has_changes = check_git_status()
        if has_changes:
            print("\n⚠️  Es gibt lokale Änderungen!")
            print("Möchtest du trotzdem pullen? (j/n): ", end="")
            if input().strip().lower() != 'j':
                print("❌ Abgebrochen.")
                return

        git_pull()

    elif choice == "2":
        check_git_status()
        git_push()

    elif choice == "3":
        # Pull dann Push
        has_changes = check_git_status()
        if has_changes:
            print("\n⚠️  Es gibt lokale Änderungen!")
            print("Möchtest du trotzdem pullen? (j/n): ", end="")
            if input().strip().lower() != 'j':
                print("❌ Abgebrochen.")
                return

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
        check_git_status()

    elif choice == "7":
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
