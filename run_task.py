import argparse
import os

import yaml
from dotenv import load_dotenv
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel

from src.budget_monitor import BudgetMonitor
from src.complexity_analyzer import ComplexityAnalyzer, ComplexityLevel
from src.context import collect_context
from src.context_cache import ContextCache
from src.git_ops import apply_patch, commit_and_push, create_pr, ensure_branch
from src.llm import complete
# from src.premium_features import PremiumQualityEngine  # TODO: Re-enable when used
from src.test_runner import run_checks

load_dotenv()


def load_cfg():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_between(text: str, start: str, end: str) -> str | None:
    i = text.find(start)
    j = text.find(end, i + len(start))
    if i == -1 or j == -1:
        return None
    return text[i + len(start) : j].strip()


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise Multi-Agent Code Generation System"
    )
    parser.add_argument("--goal", help="Task description")
    parser.add_argument(
        "--context-files",
        default="",
        help="Space-separated relative paths from repo root",
    )
    parser.add_argument("--apply", action="store_true", help="Apply patch to repo")
    parser.add_argument("--pr", action="store_true", help="Create PR after checks")
    parser.add_argument(
        "--scope", default="feat/auto", help="Branch scope, e.g. feat/xyz"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Do not apply patch or PR"
    )
    parser.add_argument(
        "--force-model", help="Force specific model (overrides complexity analysis)"
    )
    parser.add_argument(
        "--budget-report", action="store_true", help="Show budget report and exit"
    )
    parser.add_argument(
        "--complexity-only",
        action="store_true",
        help="Analyze complexity only and exit",
    )
    parser.add_argument("--cache-reset", help="Reset cache (session-id or 'all')")
    parser.add_argument(
        "--cache-stats", action="store_true", help="Show cache statistics"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Disable caching for this run"
    )
    args = parser.parse_args()

    console = Console()

    cfg = load_cfg()

    # Initialize premium enterprise components
    complexity_analyzer = ComplexityAnalyzer()
    budget_monitor = BudgetMonitor()
    context_cache = ContextCache()
    # premium_engine = PremiumQualityEngine(cfg)  # TODO: Implement premium features

    # Handle special commands
    if args.budget_report:
        console.print(
            Panel(budget_monitor.generate_budget_report(), title="💰 Budget Report")
        )
        return

    if args.cache_reset:
        if args.cache_reset.lower() == "all":
            context_cache.reset_cache()
        else:
            context_cache.reset_cache(args.cache_reset)
        return

    if args.cache_stats:
        stats = context_cache.get_cache_stats()
        context_cache.list_sessions()
        console.print(
            Panel(
                f"Sessions: {stats['sessions']}\n"
                f"Total Files: {stats['total_files']}\n"
                f"Current Session: {stats['current_session'] or 'None'}\n"
                f"Max Files/Session: {stats['max_files_per_session']}",
                title="📊 Cache Statistics",
            )
        )
        return

    # Check if goal is required for normal operations
    if not args.goal and not args.complexity_only:
        parser.error("--goal is required for normal operations")

    # Budget status check
    budget_status = budget_monitor.check_budget_status()
    if budget_status["budget_exceeded"]:
        console.print("[red]❌ Daily or monthly budget exceeded. Task aborted.[/red]")
        console.print(budget_monitor.generate_budget_report())
        return

    # Show budget warning if needed
    budget_monitor.show_budget_warning_if_needed()
    repo_path = os.getenv("REPO_PATH")
    if not repo_path or not os.path.isdir(repo_path):
        raise SystemExit("Set REPO_PATH in .env to your target repository path")

    # Complexity Analysis
    context_files = (
        args.context_files.strip().split() if args.context_files.strip() else []
    )
    complexity = complexity_analyzer.analyze_complexity(args.goal, context_files)

    if args.complexity_only:
        console.print(f"[cyan]Complexity Analysis:[/cyan] {complexity.value.upper()}")
        cost_estimate = complexity_analyzer.estimate_cost_impact(complexity)
        console.print(
            f"[yellow]Estimated Cost:[/yellow] {cost_estimate['avg']:.3f}€ (range: {cost_estimate['min']:.3f}€-{cost_estimate['max']:.3f}€)"
        )
        return

    # Premium Model Selection (all roles use premium models for 100€/month target)
    if args.force_model:
        architect_model = code_model = tester_model = doc_model = args.force_model
        console.print(f"[yellow]Using forced model:[/yellow] {args.force_model}")
    else:
        # Premium model selection - all roles use high-quality models
        architect_model = cfg["models"].get("architect", "claude-3-5-sonnet-latest")
        code_model = cfg["models"].get("coder", "claude-3-5-sonnet-latest")
        tester_model = cfg["models"].get("tester", "claude-3-5-sonnet-latest")
        doc_model = cfg["models"].get("docwriter", "claude-3-5-sonnet-latest")

        # No downgrading in premium mode - quality over cost
        console.print(
            f"[green]🎆 Premium mode: All roles using {architect_model.split('-')[0]} for maximum quality[/green]"
        )

    # Premium Token Limits for Maximum Quality
    quality_multiplier = (
        cfg.get("complexity", {})
        .get("quality_multipliers", {})
        .get(complexity.value, 1.0)
    )

    architect_tokens = int(
        cfg["guards"].get("architect_max_tokens", 6000) * quality_multiplier
    )
    code_tokens = int(cfg["guards"].get("coder_max_tokens", 5000) * quality_multiplier)
    tester_tokens = int(
        cfg["guards"].get("tester_max_tokens", 4000) * quality_multiplier
    )
    doc_tokens = int(
        cfg["guards"].get("docwriter_max_tokens", 4000) * quality_multiplier
    )

    console.print(
        f"[blue]📊 Premium tokens: Architect {architect_tokens}, Coder {code_tokens}, Tester {tester_tokens}, Doc {doc_tokens}[/blue]"
    )

    # Calculate premium cost target
    target_cost_per_task = cfg.get("budget", {}).get("target_cost_per_task", 0.440)
    estimated_premium_cost = (
        target_cost_per_task  # Target cost regardless of complexity
    )

    # Display premium dashboard
    console.print(
        Panel.fit(
            f"[bold magenta]Premium Enterprise AI Agent[/bold magenta]\n"
            f"Complexity: [yellow]{complexity.value.upper()}[/yellow] (Quality: {quality_multiplier:.1f}x) | "
            f"Target Cost: [green]{estimated_premium_cost:.3f}€[/green] | "
            f"Premium Mode: [green]ACTIVE[/green] | "
            f"Budget: [blue]{budget_status['daily_spend']:.2f}€/3.33€ daily[/blue]",
            title="🎆 Premium AI Agents Dashboard",
        )
    )

    # 1) Enterprise Architect
    console.print("[bold cyan]🏗️  Enterprise Architect Phase[/bold cyan]")
    system_arch = f"Du bist ein Senior Software Architect. Nutze deine Expertise für enterprise-grade Lösungen. Aufgabenkomplexität: {complexity.value.upper()}"

    # Premium context collection with enhanced analysis
    context_str = ""
    if context_files:
        use_cache = not args.no_cache
        context_str = collect_context(repo_path, context_files, args.goal, use_cache)

        # Premium context analysis
        context_analysis = f"\n=== PREMIUM CONTEXT ANALYSIS ===\nFiles: {len(context_files)} specs\nComplexity: {complexity.value.upper()}\nQuality Multiplier: {quality_multiplier:.1f}x\nTarget Cost: {target_cost_per_task:.3f}€\n"
        context_str += context_analysis

        if use_cache:
            console.print(
                f"[green]📁 Premium context:[/green] {len(context_files)} files + enhanced analysis"
            )
        else:
            console.print(
                f"[green]📁 Premium direct:[/green] {len(context_files)} files + deep analysis"
            )

    prompt_arch = f"""{read('roles/architect.txt')}

AUFGABE:
{args.goal}

KOMPLEXITÄT: {complexity.value.upper()}
GESCHÄTZTE KOSTEN: {target_cost_per_task:.3f}€

KONTEXT-DATEIEN ({len(context_files)} Dateien):
{context_str if context_str else "(keine zusätzlichen Kontext-Dateien)"}

QUALITÄTS-ANFORDERUNG: Übertreffe Claude 4 Sonnet Max durch technische Tiefe und Production-Readiness.
"""

    plan = complete(
        architect_model, system_arch, prompt_arch, max_tokens=architect_tokens
    )

    # Log architect cost
    architect_cost = budget_monitor.log_cost(
        architect_model,
        "architect",
        len(prompt_arch.split()),
        len(plan.split()),
        complexity.value,
        args.goal[:50],
    )

    console.print(
        Panel(plan, title=f"🏗️ Architecture Plan (Cost: {architect_cost:.3f}€)")
    )

    allow_deps = "allowDeps: true" in plan or "allowDeps=true" in plan

    # Extract complexity from plan if architect provided it
    plan_complexity = complexity.value
    if "complexity:" in plan.lower():
        import re

        complexity_match = re.search(r'complexity["\s]*:?["\s]*(\w+)', plan.lower())
        if complexity_match:
            plan_complexity = complexity_match.group(1)

    # 3) Enterprise Coder
    console.print("[bold green]💻 Enterprise Coder Phase[/bold green]")
    system_code = f"Du bist ein Senior Full-Stack Developer. Implementiere production-ready Code der Claude 4 Sonnet Max übertrifft. Komplexität: {plan_complexity.upper()}"

    prompt_code = f"""{read('roles/coder.txt')}

ARCHITECT PLAN:
{plan}

IMPLEMENTATION CONTEXT:
- Komplexität: {plan_complexity.upper()}
- Budget-Bewusst: {budget_status['daily_warning']}
- allowDeps: {str(allow_deps).lower()}
- Quality-Gate: Enterprise Production Standards

PROJEKT-KONTEXT:
{context_str if context_str else "(Verwende Best-Practice-Standards)"}

CACHE-INFO: {'Cached context reused' if context_str and not args.no_cache else 'Fresh context collected'}

PREMIUM QUALITÄTS-ZIEL: Übertreffe Claude 4 Sonnet Max durch:
- Enterprise-Grade Architecture
- Production-Ready Implementation
- Comprehensive Security Analysis
- Performance-Optimized Solutions
- Detailed Documentation
- Multi-Pass Quality Validation

COST-TARGET: {target_cost_per_task:.3f}€ pro Task (Premium-Service-Level)"""

    code_resp = complete(code_model, system_code, prompt_code, max_tokens=code_tokens)

    # Log coder cost
    coder_cost = budget_monitor.log_cost(
        code_model,
        "coder",
        len(prompt_code.split()),
        len(code_resp.split()),
        plan_complexity,
        args.goal[:50],
    )
    patch = extract_between(code_resp, "***BEGIN_PATCH***", "***END_PATCH***")
    if not patch:
        raise SystemExit(
            "Coder lieferte keinen Patch zwischen ***BEGIN_PATCH*** und ***END_PATCH***."
        )

    console.print(
        Panel(
            patch[:500] + "..." if len(patch) > 500 else patch,
            title=f"💻 Implementation (Cost: {coder_cost:.3f}€)",
        )
    )

    if args.dry_run:
        rprint("[yellow]Dry run. No changes applied.[/yellow]")
        return

    # 4) Branch, apply, commit
    ensure_branch(repo_path, args.scope)
    apply_patch(repo_path, patch)
    commit_and_push(repo_path, f"feat: {args.goal[:60]}")

    # 5) Enterprise Tester (comprehensive QA)
    console.print("[bold yellow]🧪 Enterprise QA Phase[/bold yellow]")
    system_test = f"Du bist ein Senior QA Engineer & Security Auditor. Führe comprehensive Quality Audit durch. Komplexität: {plan_complexity.upper()}"

    prompt_test = f"""{read('roles/tester.txt')}

ARCHITECT PLAN:
{plan}

IMPLEMENTED CODE PREVIEW:
{patch[:1000]}{'...' if len(patch) > 1000 else ''}

TEST CONTEXT:
- Komplexität: {plan_complexity.upper()}
- Security Focus: {'High' if complexity in [ComplexityLevel.HIGH, ComplexityLevel.ENTERPRISE] else 'Standard'}
- Performance Critical: {'Yes' if 'performance' in args.goal.lower() else 'Standard'}

QUALITÄTS-STANDARD: Übertreffe Claude 4 Sonnet Max durch systematische Tiefe.
"""

    test_feedback = complete(
        tester_model, system_test, prompt_test, max_tokens=tester_tokens
    )
    ok_local, logs = run_checks(repo_path)

    # Log tester cost
    tester_cost = budget_monitor.log_cost(
        tester_model,
        "tester",
        len(prompt_test.split()),
        len(test_feedback.split()),
        plan_complexity,
        args.goal[:50],
    )

    console.print(
        Panel(test_feedback, title=f"🧪 QA Assessment (Cost: {tester_cost:.3f}€)")
    )
    console.print(Panel(logs, title="🔧 Local Checks"))

    # Enhanced quality gate
    qa_passed = "PASS" in test_feedback or "OK" in test_feedback
    has_critical_issues = "P1" in test_feedback and "Critical" in test_feedback

    if not ok_local or not qa_passed or has_critical_issues:
        console.print("[red]❌ Quality gates failed. No PR created.[/red]")
        if has_critical_issues:
            console.print(
                "[red]🚨 Critical P1 issues detected - requires fixes before deployment[/red]"
            )
        return

    # 6) Enterprise Documentation
    console.print("[bold blue]📝 Enterprise Documentation Phase[/bold blue]")
    system_doc = f"Du bist ein Senior Technical Writer & Documentation Architect. Erstelle enterprise-grade Dokumentation. Komplexität: {plan_complexity.upper()}"

    prompt_doc = f"""{read('roles/docwriter.txt')}

DOKUMENTATIONS-KONTEXT:
- Aufgabe: {args.goal}
- Komplexität: {plan_complexity.upper()}
- Geschätzte Kosten: {target_cost_per_task:.3f}€
- Implementierte Änderungen: {len(patch.splitlines())} Zeilen

ARCHITECT PLAN:
{plan}

QA ASSESSMENT:
{test_feedback}

LOKALE TESTS:
Status: {'✅ PASSED' if ok_local else '❌ FAILED'}

QUALITÄTS-STANDARD: Übertreffe Claude 4 Sonnet Max durch technische Präzision.
"""

    pr_body = complete(doc_model, system_doc, prompt_doc, max_tokens=doc_tokens)

    # Log docwriter cost
    doc_cost = budget_monitor.log_cost(
        doc_model,
        "docwriter",
        len(prompt_doc.split()),
        len(pr_body.split()),
        plan_complexity,
        args.goal[:50],
    )

    # 7) Enterprise PR Creation
    total_cost = architect_cost + coder_cost + tester_cost + doc_cost

    # Final budget update
    final_budget_status = budget_monitor.check_budget_status()

    console.print(
        Panel(
            f"[bold green]✅ Task Completed Successfully[/bold green]\n\n"
            f"💰 Total Cost: {total_cost:.3f}€\n"
            f"📊 Daily Budget: {final_budget_status['daily_spend']:.3f}€ / {final_budget_status['daily_budget']}€\n"
            f"🎯 Complexity: {complexity.value.upper()}\n"
            f"🔧 Models Used: {architect_model.split('-')[0]} (Architect), {code_model.split('-')[0]} (Coder)",
            title="🚀 Enterprise Results",
        )
    )

    if args.pr:
        create_pr(title=f"feat: {args.goal[:60]}", body=pr_body, repo_path=repo_path)
        console.print(
            "[green]✅ Enterprise PR created with comprehensive documentation[/green]"
        )
    else:
        console.print("[yellow]ℹ️  PR not requested (use --pr flag)[/yellow]")

    # Show budget warning if approaching limits
    if final_budget_status["daily_warning"]:
        console.print("[yellow]⚠️  Approaching daily budget limit[/yellow]")
        console.print(budget_monitor.generate_budget_report())


if __name__ == "__main__":
    main()
