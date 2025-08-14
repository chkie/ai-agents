# AI Agents - Multi-Agent Code Generation System

Ein Python-basiertes Multi-Agent-System für automatisierte Code-Generierung mit Architect → Coder → Tester → DocWriter Workflow.

## Schneller Start (macOS + fish)

### 1. Environment Setup

```fish
# Virtual Environment aktivieren
. .venv/bin/activate.fish

# Dependencies installieren
pip install -r requirements.txt
```

### 2. Konfiguration

```fish
# .env aus Template erstellen
cp .env.example .env

# .env bearbeiten und ausfüllen:
# ANTHROPIC_API_KEY=your_actual_key_here
# REPO_PATH=/absolute/path/to/your/target/repo
```

### 3. Usage

```fish
# Dry-Run (zeigt nur den generierten Patch)
python run_task.py --goal "Add dark mode toggle to navbar" --dry-run

# Real-Run mit PR-Erstellung
python run_task.py --goal "Add dark mode toggle to navbar" --apply --pr --scope "feat/dark-mode"

# Mit zusätzlichen Kontext-Dateien
python run_task.py --goal "Fix login validation" --context-files "src/routes/login/+page.svelte src/lib/auth.ts" --apply
```

### Kontext-Dateien: Dateien, Ordner, Globs

Das `--context-files` Argument akzeptiert verschiedene Spezifikationen:

```fish
# Einzelne Dateien
--context-files "src/app.ts src/lib/utils.js"

# Ganze Ordner (alle erlaubten Dateitypen)
--context-files "src/components src/lib"

# Glob-Muster
--context-files "src/routes/**/*.svelte src/lib/components/ui/*.ts"
```

## Features

- **Package Manager Auto-Detection**: Unterstützt npm, yarn, pnpm, bun automatisch via Lockfiles
- **Sicherheit**: Branch-Name-Validation und Commit-Message-Sanitizing
- **Fallbacks**: Graceful Handling wenn JS-Projekt-Tools fehlen
- **Konfigurierbar**: Überschreibbare Test-Commands in `config.yaml`
- **Budget-Control**: Token-Limits und Kostenüberwachung
