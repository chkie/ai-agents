"""
Adaptive Complexity Analysis for Enterprise-Grade Multi-Agent System
Analyzes task complexity to optimize model selection and token allocation.
"""

import re
from enum import Enum
from typing import Dict, List

import yaml


class ComplexityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ENTERPRISE = "enterprise"


class ComplexityAnalyzer:
    """Analyzes task complexity for optimal model and token allocation."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.complexity_indicators = self.config.get("complexity", {}).get(
            "indicators", {}
        )
        self.thresholds = self.config.get("complexity", {}).get("thresholds", {})

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration with fallback defaults."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_config()

    def _default_config(self) -> Dict:
        """Default configuration if config.yaml is not available."""
        return {
            "complexity": {
                "indicators": {
                    "high": [
                        "architecture",
                        "refactor",
                        "migration",
                        "security",
                        "performance",
                        "integration",
                    ],
                    "medium": ["feature", "component", "api", "database", "ui"],
                    "low": ["fix", "style", "docs", "config", "typo", "comment"],
                },
                "thresholds": {
                    "context_files_high": 8,
                    "context_files_medium": 3,
                    "goal_words_high": 15,
                    "goal_words_medium": 8,
                },
            }
        }

    def analyze_complexity(
        self, goal: str, context_files: List[str] = None
    ) -> ComplexityLevel:
        """
        Analyze task complexity based on goal description and context.

        Args:
            goal: Task description
            context_files: List of context files

        Returns:
            ComplexityLevel enum value
        """
        if context_files is None:
            context_files = []

        # Analyze goal text for complexity indicators
        goal_complexity = self._analyze_goal_complexity(goal)

        # Analyze context size
        context_complexity = self._analyze_context_complexity(context_files)

        # Combine scores for final assessment
        final_complexity = self._combine_complexity_scores(
            goal_complexity, context_complexity
        )

        return final_complexity

    def _analyze_goal_complexity(self, goal: str) -> ComplexityLevel:
        """Analyze complexity based on goal description."""
        goal_lower = goal.lower()
        word_count = len(goal.split())

        # Check for high complexity indicators
        high_indicators = self.complexity_indicators.get("high", [])
        medium_indicators = self.complexity_indicators.get("medium", [])
        low_indicators = self.complexity_indicators.get("low", [])

        high_matches = sum(
            1 for indicator in high_indicators if indicator in goal_lower
        )
        medium_matches = sum(
            1 for indicator in medium_indicators if indicator in goal_lower
        )
        low_matches = sum(1 for indicator in low_indicators if indicator in goal_lower)

        # Enterprise-level indicators
        enterprise_patterns = [
            r"migrate.*database",
            r"refactor.*architecture",
            r"implement.*security.*framework",
            r"performance.*optimization.*across",
            r"integrate.*multiple.*services",
        ]

        if any(re.search(pattern, goal_lower) for pattern in enterprise_patterns):
            return ComplexityLevel.ENTERPRISE

        # Word count thresholds
        if word_count > self.thresholds.get("goal_words_high", 15):
            if high_matches >= 2:
                return ComplexityLevel.ENTERPRISE
            return ComplexityLevel.HIGH
        elif word_count > self.thresholds.get("goal_words_medium", 8):
            if high_matches >= 1:
                return ComplexityLevel.HIGH
            return ComplexityLevel.MEDIUM

        # Indicator-based assessment
        if high_matches >= 2:
            return ComplexityLevel.HIGH
        elif high_matches >= 1 or medium_matches >= 2:
            return ComplexityLevel.MEDIUM
        elif medium_matches >= 1 or low_matches >= 1:
            return ComplexityLevel.LOW

        # Default for simple tasks
        return ComplexityLevel.LOW

    def _analyze_context_complexity(self, context_files: List[str]) -> ComplexityLevel:
        """Analyze complexity based on context files."""
        file_count = len(context_files)

        if file_count > self.thresholds.get("context_files_high", 8):
            return ComplexityLevel.HIGH
        elif file_count > self.thresholds.get("context_files_medium", 3):
            return ComplexityLevel.MEDIUM
        elif file_count > 0:
            return ComplexityLevel.LOW

        return ComplexityLevel.LOW

    def _combine_complexity_scores(
        self, goal_complexity: ComplexityLevel, context_complexity: ComplexityLevel
    ) -> ComplexityLevel:
        """Combine goal and context complexity scores."""
        complexity_values = {
            ComplexityLevel.LOW: 1,
            ComplexityLevel.MEDIUM: 2,
            ComplexityLevel.HIGH: 3,
            ComplexityLevel.ENTERPRISE: 4,
        }

        goal_value = complexity_values[goal_complexity]
        context_value = complexity_values[context_complexity]

        # Use weighted average (goal is more important)
        combined_value = (goal_value * 0.7) + (context_value * 0.3)

        if combined_value >= 3.5:
            return ComplexityLevel.ENTERPRISE
        elif combined_value >= 2.5:
            return ComplexityLevel.HIGH
        elif combined_value >= 1.5:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.LOW

    def get_model_recommendation(self, complexity: ComplexityLevel) -> str:
        """Get recommended model based on complexity."""
        model_mapping = {
            ComplexityLevel.LOW: self.config.get("models", {}).get(
                "efficient", "claude-3-5-haiku-latest"
            ),
            ComplexityLevel.MEDIUM: self.config.get("models", {}).get(
                "advanced", "claude-3-5-sonnet-latest"
            ),
            ComplexityLevel.HIGH: self.config.get("models", {}).get(
                "premium", "gpt-4o-2024-08-06"
            ),
            ComplexityLevel.ENTERPRISE: self.config.get("models", {}).get(
                "premium", "gpt-4o-2024-08-06"
            ),
        }

        return model_mapping[complexity]

    def get_token_limit(
        self, complexity: ComplexityLevel, role: str = "default"
    ) -> int:
        """Get token limit based on complexity and role."""
        base_limits = {
            ComplexityLevel.LOW: self.config.get("guards", {}).get(
                "efficient_max_output_tokens", 1200
            ),
            ComplexityLevel.MEDIUM: self.config.get("guards", {}).get(
                "advanced_max_output_tokens", 3200
            ),
            ComplexityLevel.HIGH: self.config.get("guards", {}).get(
                "premium_max_output_tokens", 4000
            ),
            ComplexityLevel.ENTERPRISE: 6000,  # Maximum for enterprise tasks
        }

        base_limit = base_limits[complexity]

        # Role-specific multipliers
        role_multipliers = {
            "architect": 1.2,  # Architects need more tokens for detailed planning
            "coder": 1.0,  # Standard implementation
            "tester": 1.1,  # Testers need extra for comprehensive analysis
            "docwriter": 0.8,  # Documentation is typically more concise
        }

        multiplier = role_multipliers.get(role.lower(), 1.0)
        return int(base_limit * multiplier)

    def estimate_cost_impact(self, complexity: ComplexityLevel) -> Dict[str, float]:
        """Estimate cost impact for budget planning."""
        # Cost estimates per complexity level (in EUR)
        cost_estimates = {
            ComplexityLevel.LOW: {"min": 0.05, "max": 0.15, "avg": 0.10},
            ComplexityLevel.MEDIUM: {"min": 0.15, "max": 0.50, "avg": 0.30},
            ComplexityLevel.HIGH: {"min": 0.50, "max": 1.50, "avg": 1.00},
            ComplexityLevel.ENTERPRISE: {"min": 1.50, "max": 5.00, "avg": 3.00},
        }

        return cost_estimates[complexity]
