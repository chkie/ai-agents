import os, argparse, yaml
from dotenv import load_dotenv
from rich import print as rprint

from src.llm import complete
from src.context import collect_context
from src.git_ops import ensure_branch, apply_patch, commit_and_push, create_pr
from src.test_runner import run_checks

load_dotenv()

def load_cfg():
    with open("config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)

def read(path: str) -> str:
    with open(path,"r",encoding="utf-8") as f:
        return f.read()

def extract_between(text: str, start: str, end: str) -> str | None:
    i = text.find(start)
    j = text.find(end, i+len(start))
    if i == -1 or j == -1: return None
    return text[i+len(start):j].strip()

def main():
    parser = argparse.ArgumentParser(description="Run a minimal multi-agent task.")
    parser.add_argument("--goal", required=True, help="Task description")
    parser.add_argument("--context-files", default="", help="Space-separated relative paths from repo root")
    parser.add_argument("--apply", action="store_true", help="Apply patch to repo")
    parser.add_argument("--pr", action="store_true", help="Create PR after checks")
    parser.add_argument("--scope", default="feat/auto", help="Branch scope, e.g. feat/xyz")
    parser.add_argument("--dry-run", action="store_true", help="Do not apply patch or PR")
    args = parser.parse_args()

    cfg = load_cfg()
    repo_path = os.getenv("REPO_PATH")
    if not repo_path or not os.path.isdir(repo_path):
        raise SystemExit("Set REPO_PATH in .env to your target repository path")

    cheap_model = cfg["models"]["cheap"]
    code_model  = cfg["models"]["code"]
    cheap_max = int(cfg["guards"]["cheap_max_output_tokens"])
    code_max  = int(cfg["guards"]["coder_max_output_tokens"])

    # 1) Architect
    system_arch = "Du bist ein praeziser Software-Architekt. Antworte in Deutsch."
    prompt_arch = f"""{read('roles/architect.txt')}

Nutzerziel:
{args.goal}

Hinweis: Erzeuge kurze, konkrete Akzeptanzkriterien. Erwarte 2-3 UI-Screenshots im PR.
"""
    plan = complete(cheap_model, system_arch, prompt_arch, max_tokens=cheap_max)
    rprint("[bold cyan]Architect Plan[/bold cyan]\n"+plan)

    allow_deps = "allowDeps: true" in plan or "allowDeps=true" in plan

    # 2) Context files (optional)
    context_str = ""
    if args.context_files.strip():
        files = args.context_files.strip().split()
        context_str = collect_context(repo_path, files)

    # 3) Coder
    system_code = "Du bist ein Senior-Entwickler. Gib ausschliesslich Unified Diffs aus."
    prompt_code = f"""{read('roles/coder.txt')}

Plan (vom Architect):
{plan}

Policy:
- allowDeps = {str(allow_deps).lower()}

Projekt-Kontext (ausgewaehlte Dateien, optional):
{context_str if context_str else "(kein zusaetzlicher Kontext uebergeben)"}"""

    code_resp = complete(code_model, system_code, prompt_code, max_tokens=code_max)
    patch = extract_between(code_resp, "***BEGIN_PATCH***", "***END_PATCH***")
    if not patch:
        raise SystemExit("Coder lieferte keinen Patch zwischen ***BEGIN_PATCH*** und ***END_PATCH***.")

    rprint("[bold magenta]Proposed Patch[/bold magenta]\n"+patch)

    if args.dry_run:
        rprint("[yellow]Dry run. No changes applied.[/yellow]")
        return

    # 4) Branch, apply, commit
    ensure_branch(repo_path, args.scope)
    apply_patch(repo_path, patch)
    commit_and_push(repo_path, f"feat: {args.goal[:60]}")

    # 5) Tester (run checks)
    system_test = "Du bist ein erfahrener QA-Ingenieur. Antworte knapp."
    prompt_test = f"""{read('roles/tester.txt')}

Plan:
{plan}
"""
    test_feedback = complete(cheap_model, system_test, prompt_test, max_tokens=cheap_max)
    ok_local, logs = run_checks(repo_path)
    rprint("[bold cyan]Tester (LLM) feedback[/bold cyan]\n"+test_feedback)
    rprint("[bold cyan]Local checks[/bold cyan]\n"+logs)

    if not ok_local or "OK" not in test_feedback:
        rprint("[red]Checks failed or acceptance not met. No PR created.[/red]")
        return

    # 6) DocWriter
    system_doc = "Du bist ein technischer Redakteur. Antworte in Markdown."
    prompt_doc = f"""{read('roles/docwriter.txt')}

Kontext:
- Ziel: {args.goal}
- Akzeptanzkriterien: Aus dem Plan
- Testergebnis (kurz): OK
"""
    pr_body = complete(cheap_model, system_doc, prompt_doc, max_tokens=cheap_max)

    # 7) PR
    if args.pr:
        create_pr(title=f"feat: {args.goal[:60]}", body=pr_body, repo_path=repo_path)
        rprint("[green]PR created.[/green]")
    else:
        rprint("[yellow]PR not requested (--pr).[/yellow]")

if __name__ == "__main__":
    main()
