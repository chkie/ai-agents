"""
Budget Monitoring and Cost Optimization for Enterprise Multi-Agent System
Tracks API costs and optimizes model selection to stay within budget constraints.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml


@dataclass
class CostEntry:
    """Individual cost tracking entry."""
    timestamp: str
    model: str
    role: str
    input_tokens: int
    output_tokens: int
    cost_eur: float
    complexity: str
    goal_summary: str


class BudgetMonitor:
    """Monitors API costs and enforces budget constraints."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.budget_config = self.config.get("budget", {})
        self.guards = self.config.get("guards", {})
        self.cost_log_path = Path(".ai_agents_costs.json")
        
        # Budget limits
        self.monthly_budget = self.guards.get("budget_cap_eur", 150.0)
        self.daily_budget = self.budget_config.get("daily_budget_eur", 5.0)
        self.task_warning_threshold = self.budget_config.get("task_budget_warning_eur", 2.0)
        
        # Cost tracking
        self.costs = self._load_cost_history()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration with fallback defaults."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {"budget": {}, "guards": {"budget_cap_eur": 150.0}}
    
    def _load_cost_history(self) -> List[CostEntry]:
        """Load cost history from persistent storage."""
        if not self.cost_log_path.exists():
            return []
        
        try:
            with open(self.cost_log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [CostEntry(**entry) for entry in data]
        except (json.JSONDecodeError, TypeError):
            return []
    
    def _save_cost_history(self):
        """Save cost history to persistent storage."""
        if not self.budget_config.get("log_costs", True):
            return
        
        data = [asdict(entry) for entry in self.costs]
        with open(self.cost_log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def estimate_task_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a task based on model and token counts."""
        # Model pricing (EUR per 1K tokens, approximate)
        pricing = {
            "gpt-4o-2024-08-06": {"input": 0.002, "output": 0.008},
            "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},
            "claude-3-5-haiku-latest": {"input": 0.0002, "output": 0.001}
        }
        
        # Default pricing for unknown models
        default_price = {"input": 0.002, "output": 0.008}
        model_price = pricing.get(model, default_price)
        
        input_cost = (input_tokens / 1000) * model_price["input"]
        output_cost = (output_tokens / 1000) * model_price["output"]
        
        return input_cost + output_cost
    
    def log_cost(self, model: str, role: str, input_tokens: int, 
                output_tokens: int, complexity: str, goal_summary: str):
        """Log a cost entry."""
        cost = self.estimate_task_cost(model, input_tokens, output_tokens)
        
        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            model=model,
            role=role,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_eur=cost,
            complexity=complexity,
            goal_summary=goal_summary[:100]  # Truncate for storage
        )
        
        self.costs.append(entry)
        self._save_cost_history()
        
        return cost
    
    def get_daily_spend(self, date: datetime = None) -> float:
        """Get total spend for a specific day."""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        
        daily_costs = [
            entry.cost_eur for entry in self.costs
            if entry.timestamp.startswith(date_str)
        ]
        
        return sum(daily_costs)
    
    def get_monthly_spend(self, date: datetime = None) -> float:
        """Get total spend for a specific month."""
        if date is None:
            date = datetime.now()
        
        month_str = date.strftime("%Y-%m")
        
        monthly_costs = [
            entry.cost_eur for entry in self.costs
            if entry.timestamp.startswith(month_str)
        ]
        
        return sum(monthly_costs)
    
    def check_budget_status(self) -> Dict[str, any]:
        """Check current budget status and warnings."""
        today_spend = self.get_daily_spend()
        month_spend = self.get_monthly_spend()
        
        # Calculate budget utilization
        daily_utilization = (today_spend / self.daily_budget) * 100
        monthly_utilization = (month_spend / self.monthly_budget) * 100
        
        # Determine warning levels
        daily_warning = daily_utilization > 80
        monthly_warning = monthly_utilization > 80
        
        # Calculate remaining budget
        remaining_daily = max(0, self.daily_budget - today_spend)
        remaining_monthly = max(0, self.monthly_budget - month_spend)
        
        return {
            "daily_spend": today_spend,
            "monthly_spend": month_spend,
            "daily_budget": self.daily_budget,
            "monthly_budget": self.monthly_budget,
            "daily_utilization": daily_utilization,
            "monthly_utilization": monthly_utilization,
            "daily_warning": daily_warning,
            "monthly_warning": monthly_warning,
            "remaining_daily": remaining_daily,
            "remaining_monthly": remaining_monthly,
            "budget_exceeded": daily_utilization >= 100 or monthly_utilization >= 100
        }
    
    def should_downgrade_model(self, estimated_cost: float) -> bool:
        """Check if model should be downgraded due to budget constraints."""
        if not self.budget_config.get("auto_downgrade_models", True):
            return False
        
        status = self.check_budget_status()
        
        # Downgrade if budget would be exceeded
        if status["remaining_daily"] < estimated_cost:
            return True
        
        # Downgrade if approaching limits
        if status["daily_utilization"] > 90 and estimated_cost > 0.5:
            return True
        
        return False
    
    def get_downgraded_model(self, original_model: str) -> str:
        """Get a more cost-effective model alternative."""
        model_hierarchy = [
            "gpt-4o-2024-08-06",           # Most expensive
            "claude-3-5-sonnet-latest",    # Medium cost
            "claude-3-5-haiku-latest"      # Most cost-effective
        ]
        
        try:
            current_index = model_hierarchy.index(original_model)
            # Move to next cheaper model
            if current_index < len(model_hierarchy) - 1:
                return model_hierarchy[current_index + 1]
        except ValueError:
            pass
        
        # Return most cost-effective if not in hierarchy
        return "claude-3-5-haiku-latest"
    
    def get_cost_analysis(self, days: int = 7) -> Dict[str, any]:
        """Get detailed cost analysis for the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        recent_costs = [
            entry for entry in self.costs
            if entry.timestamp > cutoff_str
        ]
        
        if not recent_costs:
            return {
                "total_cost": 0, 
                "average_daily": 0, 
                "days_analyzed": days,
                "task_count": 0,
                "model_breakdown": {}, 
                "role_breakdown": {},
                "complexity_breakdown": {},
                "cost_per_task": 0
            }
        
        total_cost = sum(entry.cost_eur for entry in recent_costs)
        average_daily = total_cost / days
        
        # Model breakdown
        model_costs = {}
        for entry in recent_costs:
            model_costs[entry.model] = model_costs.get(entry.model, 0) + entry.cost_eur
        
        # Role breakdown
        role_costs = {}
        for entry in recent_costs:
            role_costs[entry.role] = role_costs.get(entry.role, 0) + entry.cost_eur
        
        # Complexity breakdown
        complexity_costs = {}
        for entry in recent_costs:
            complexity_costs[entry.complexity] = complexity_costs.get(entry.complexity, 0) + entry.cost_eur
        
        task_count = len(recent_costs)
        return {
            "total_cost": total_cost,
            "average_daily": average_daily,
            "days_analyzed": days,
            "task_count": task_count,
            "model_breakdown": model_costs,
            "role_breakdown": role_costs,
            "complexity_breakdown": complexity_costs,
            "cost_per_task": total_cost / task_count if task_count > 0 else 0
        }
    
    def generate_budget_report(self) -> str:
        """Generate a formatted budget report."""
        status = self.check_budget_status()
        analysis = self.get_cost_analysis()
        
        daily_status = '🔴 EXCEEDED' if status['daily_utilization'] >= 100 else '🟡 WARNING' if status['daily_warning'] else '🟢 OK'
        monthly_status = '🔴 EXCEEDED' if status['monthly_utilization'] >= 100 else '🟡 WARNING' if status['monthly_warning'] else '🟢 OK'
        
        report = f"""📊 AI Agents Budget Report
========================

💰 Current Budget Status:
- Daily: {status['daily_spend']:.3f}€ / {status['daily_budget']:.2f}€ ({status['daily_utilization']:.1f}%)
- Monthly: {status['monthly_spend']:.2f}€ / {status['monthly_budget']:.2f}€ ({status['monthly_utilization']:.1f}%)

⚠️  Warnings:
- Daily Budget: {daily_status}
- Monthly Budget: {monthly_status}

📈 7-Day Analysis:
- Total Cost: {analysis['total_cost']:.3f}€
- Average Daily: {analysis['average_daily']:.3f}€
- Tasks Completed: {analysis['task_count']}
- Cost per Task: {analysis['cost_per_task']:.3f}€

🔧 Model Usage:
"""
        
        for model, cost in analysis['model_breakdown'].items():
            percentage = (cost / analysis['total_cost'] * 100) if analysis['total_cost'] > 0 else 0
            report += f"- {model}: {cost:.3f}€ ({percentage:.1f}%)\n"
        
        report += "\n👥 Role Distribution:\n"
        for role, cost in analysis['role_breakdown'].items():
            percentage = (cost / analysis['total_cost'] * 100) if analysis['total_cost'] > 0 else 0
            report += f"- {role}: {cost:.3f}€ ({percentage:.1f}%)\n"
        
        return report
