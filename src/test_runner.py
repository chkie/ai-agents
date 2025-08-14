import subprocess
import pathlib
import json
import yaml

def detect_pm(repo_path: str) -> dict:
    """Detect package manager and available scripts from repo."""
    root = pathlib.Path(repo_path)
    
    # Check for lockfiles to determine package manager
    pm = None
    if (root / "pnpm-lock.yaml").exists():
        pm = "pnpm"
    elif (root / "yarn.lock").exists():
        pm = "yarn"
    elif (root / "package-lock.json").exists():
        pm = "npm"
    elif (root / "bun.lockb").exists():
        pm = "bun"
    
    # If no JS project detected
    if pm is None and not (root / "package.json").exists():
        return {"pm": None, "scripts": [], "is_js": False}
    
    # Default to npm if package.json exists but no lockfile
    if pm is None:
        pm = "npm"
    
    # Read package.json to check available scripts
    available_scripts = []
    try:
        with open(root / "package.json", "r", encoding="utf-8") as f:
            pkg = json.load(f)
            scripts = pkg.get("scripts", {})
            for script in ["check", "lint", "test"]:
                if script in scripts:
                    available_scripts.append(script)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    return {"pm": pm, "scripts": available_scripts, "is_js": True}

def build_commands(pm_info: dict, overrides: list = None) -> list:
    """Build command list based on package manager and available scripts."""
    if overrides:
        return overrides
    
    if not pm_info["is_js"]:
        return []
    
    pm = pm_info["pm"]
    available = pm_info["scripts"]
    commands = []
    
    # Command mapping per package manager
    cmd_map = {
        "npm": {
            "check": ["npm", "run", "check"],
            "lint": ["npm", "run", "lint"],
            "test": ["npm", "run", "test", "--", "-runInBand"]
        },
        "yarn": {
            "check": ["yarn", "check"],
            "lint": ["yarn", "lint"],
            "test": ["yarn", "test", "-runInBand"]
        },
        "pnpm": {
            "check": ["pnpm", "check"],
            "lint": ["pnpm", "lint"],
            "test": ["pnpm", "test", "-", "-runInBand"]
        },
        "bun": {
            "check": ["bun", "run", "check"],
            "lint": ["bun", "run", "lint"],
            "test": ["bun", "run", "test", "-runInBand"]
        }
    }
    
    for script in ["check", "lint", "test"]:
        if script in available and pm in cmd_map:
            commands.append(cmd_map[pm][script])
    
    return commands

def run_checks(repo_path: str) -> tuple[bool, str]:
    # Load config for overrides
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            runner_cfg = cfg.get("runner", {})
            pm_override = runner_cfg.get("package_manager", "auto")
            cmd_overrides = runner_cfg.get("test_commands", [])
    except (FileNotFoundError, yaml.YAMLError):
        pm_override = "auto"
        cmd_overrides = []
    
    # Detect package manager and build commands
    pm_info = detect_pm(repo_path)
    
    if not pm_info["is_js"]:
        return True, "No JS project detected; checks skipped."
    
    # Apply manual override if specified
    if pm_override != "auto":
        pm_info["pm"] = pm_override
    
    cmds = build_commands(pm_info, cmd_overrides if cmd_overrides else None)
    
    if not cmds:
        return True, "No test commands available; checks skipped."
    
    log = []
    all_ok = True
    for c in cmds:
        p = subprocess.run(c, cwd=repo_path, text=True, capture_output=True)
        ok = (p.returncode == 0)
        all_ok = all_ok and ok
        log.append(f"$ {' '.join(c)}\n{p.stdout}\n{p.stderr}\n")
        if not ok:
            break
    return all_ok, "\n".join(log)
