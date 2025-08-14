import subprocess, tempfile
import re

def validate_branch(name: str):
    """Validate branch name to prevent injection attacks."""
    if not re.match(r'^[A-Za-z0-9._/-]{1,100}$', name):
        raise ValueError(f"Invalid branch name: '{name}'. Must match [A-Za-z0-9._/-] and be 1-100 chars.")
    
    # Additional safety checks
    if name.startswith('/') or name.endswith('/'):
        raise ValueError(f"Branch name cannot start or end with '/': '{name}'")
    if '..' in name or '//' in name:
        raise ValueError(f"Branch name cannot contain '..' or '//': '{name}'")
    if name in ['.', '..']:
        raise ValueError(f"Branch name cannot be '.' or '..': '{name}'")

def sanitize_commit_message(msg: str) -> str:
    """Sanitize commit message to remove control characters."""
    # Remove control characters and replace newlines with spaces
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', msg)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    return sanitized[:200]  # Limit length

def run(cmd, cwd=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p

def ensure_branch(repo_path: str, branch: str):
    validate_branch(branch)
    run(["git","-C",repo_path,"fetch","-p"])
    run(["git","-C",repo_path,"checkout","-b", branch])

def apply_patch(repo_path: str, patch_text: str):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".patch") as f:
        f.write(patch_text)
        patch_file = f.name
    run(["git","-C",repo_path,"apply","--whitespace=fix","--index", patch_file])

def commit_and_push(repo_path: str, message: str):
    message = sanitize_commit_message(message)
    run(["git","-C",repo_path,"commit","-m", message, "--no-verify"])
    run(["git","-C",repo_path,"push","-u","origin","HEAD"])

def create_pr(title: str, body: str, repo_path: str):
    run(["gh","pr","create","--title", title, "--body", body], cwd=repo_path)
