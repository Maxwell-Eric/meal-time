# meal_time/services/timeline_service.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

from meal_time.models.recipe import Recipe
from config import Config


@dataclass
class TimelineStep:
    """Structured representation of a cooking step with timing"""
    text: str
    duration: int
    start_time: datetime
    end_time: datetime
    recipe_name: str
    step_number: int
    recipe_color: str
    is_prep: bool = False
    is_cooking: bool = False
    can_multitask: bool = False
    order: int = 0
    time_gap: float = 0.0


class TimelineService:
    """Service for generating cooking timelines"""

    def __init__(self):
        self.config = Config()

    def generate_timeline(self, recipes: List[Recipe], target_time: datetime) -> List[TimelineStep]:
        """Generate a coordinated timeline for multiple recipes"""
        if not recipes:
            return []

        all_steps = []

        for idx, recipe in enumerate(recipes):
            recipe_steps = self._process_single_recipe(
                recipe,
                target_time,
                idx
            )
            all_steps.extend(recipe_steps)

        # Sort by start time and add metadata
        sorted_steps = sorted(all_steps, key=lambda x: x.start_time)
        return self._add_timeline_metadata(sorted_steps)

    def _process_single_recipe(self, recipe: Recipe, target_time: datetime, color_index: int) -> List[TimelineStep]:
        """Process a single recipe into timed steps"""
        if not recipe.steps or not recipe.step_times:
            return []

        if len(recipe.steps) != len(recipe.step_times):
            return []

        steps = []
        current_end_time = target_time
        recipe_color = self.config.RECIPE_COLORS[color_index % len(self.config.RECIPE_COLORS)]

        # Work backwards through steps
        for i, (step_text, duration) in enumerate(reversed(list(zip(recipe.steps, recipe.step_times)))):
            step_number = len(recipe.steps) - i
            start_time = current_end_time - timedelta(minutes=duration)

            timeline_step = TimelineStep(
                text=step_text,
                duration=duration,
                start_time=start_time,
                end_time=current_end_time,
                recipe_name=recipe.name,
                step_number=step_number,
                recipe_color=recipe_color,
                is_prep=self._is_prep_step(step_text),
                is_cooking=self._is_cooking_step(step_text),
                can_multitask=self._can_multitask(step_text)
            )

            steps.append(timeline_step)
            current_end_time = start_time

        return list(reversed(steps))

    def _add_timeline_metadata(self, steps: List[TimelineStep]) -> List[TimelineStep]:
        """Add ordering and gap information to timeline steps"""
        for i, step in enumerate(steps):
            step.order = i + 1

            if i > 0:
                prev_step = steps[i - 1]
                gap_seconds = (step.start_time - prev_step.end_time).total_seconds()
                step.time_gap = gap_seconds / 60  # Convert to minutes

        return steps

    def _is_prep_step(self, step_text: str) -> bool:
        """Identify preparation steps"""
        return any(keyword in step_text.lower() for keyword in self.config.PREP_KEYWORDS)

    def _is_cooking_step(self, step_text: str) -> bool:
        """Identify active cooking steps"""
        return any(keyword in step_text.lower() for keyword in self.config.COOKING_KEYWORDS)

    def _can_multitask(self, step_text: str) -> bool:
        """Identify steps that allow multitasking"""
        return any(keyword in step_text.lower() for keyword in self.config.MULTITASK_KEYWORDS)

    def get_timeline_summary(self, steps: List[TimelineStep], target_time: datetime) -> Dict:
        """Generate summary statistics for a timeline"""
        if not steps:
            return self._empty_summary()

        start_time = min(step.start_time for step in steps)
        total_time = (target_time - start_time).total_seconds() / 60

        recipes = list(set(step.recipe_name for step in steps))
        prep_steps = sum(1 for step in steps if step.is_prep)
        cooking_steps = sum(1 for step in steps if step.is_cooking)
        multitask_steps = sum(1 for step in steps if step.can_multitask)

        return {
            "total_time": int(total_time),
            "start_time": start_time,
            "end_time": target_time,
            "recipes": recipes,
            "total_steps": len(steps),
            "prep_steps": prep_steps,
            "cooking_steps": cooking_steps,
            "multitask_opportunities": multitask_steps
        }

    def _empty_summary(self) -> Dict:
        """Return empty summary for no steps"""
        return {
            "total_time": 0,
            "start_time": None,
            "end_time": None,
            "recipes": [],
            "total_steps": 0,
            "prep_steps": 0,
            "cooking_steps": 0,
            "multitask_opportunities": 0
        }

    def validate_timeline(self, steps: List[TimelineStep], current_time: datetime) -> Dict:
        """Validate if timeline is feasible"""
        if not steps:
            return {"valid": True, "issues": []}

        issues = []
        earliest_start = min(step.start_time for step in steps)

        if earliest_start <= current_time:
            minutes_past = (current_time - earliest_start).total_seconds() / 60
            issues.append({
                "type": "past_start_time",
                "message": f"Timeline requires starting {minutes_past:.0f} minutes ago",
                "severity": "error"
            })

        # Check for overlapping high-attention steps
        active_cooking_steps = [s for s in steps if s.is_cooking and not s.can_multitask]
        for i, step1 in enumerate(active_cooking_steps):
            for step2 in active_cooking_steps[i + 1:]:
                if (step1.start_time < step2.end_time and
                        step2.start_time < step1.end_time and
                        step1.recipe_name != step2.recipe_name):
                    issues.append({
                        "type": "overlapping_active_steps",
                        "message": f"Active cooking steps overlap: {step1.recipe_name} and {step2.recipe_name}",
                        "severity": "warning"
                    })

        return {
            "valid": len([i for i in issues if i["severity"] == "error"]) == 0,
            "issues": issues
        }
