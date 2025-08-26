import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from src.meal_time_logic.ml.step_time_predictor import StepTimePredictor


@dataclass
class ParsedStep:
    """Represents a step with extracted timing information"""
    text: str
    duration_minutes: Optional[int]
    original_text: str
    confidence: str  # 'extracted', 'predicted', 'user_set'
    time_phrases: List[str] = None  # The actual phrases found like "10 minutes", "1 hour"


class StepTimeParser:
    """Service for parsing time information from recipe step text"""

    def __init__(self):
        self.predictor = StepTimePredictor()

        # Time extraction patterns
        self.time_patterns = [
            # Standard formats: "10 minutes", "1 hour", "30 seconds"
            r'(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)',

            # Range formats: "10-15 minutes", "1-2 hours"
            r'(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)',

            # Fractional: "1/2 hour", "1½ minutes"
            r'(\d+\/\d+|\d+½|\d+¼|\d+¾)\s*(minutes?|mins?|hours?|hrs?)',

            # "About/approximately" formats
            r'(?:about|approximately|roughly|around)\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?)',

            # Until done: "cook until golden", "bake until done" (these will need prediction)
            r'(?:cook|bake|simmer|boil)\s+until\s+(?:golden|done|tender|cooked|set)',
        ]

        # Compile patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.time_patterns]

        # Unit conversions to minutes
        self.unit_conversions = {
            'second': 1 / 60, 'seconds': 1 / 60, 'sec': 1 / 60, 'secs': 1 / 60,
            'minute': 1, 'minutes': 1, 'min': 1, 'mins': 1,
            'hour': 60, 'hours': 60, 'hr': 60, 'hrs': 60,
        }

    def parse_step_times(self, step_text: str) -> List[ParsedStep]:
        """
        Parse a step and return list of ParsedSteps.
        If multiple times found, splits into separate steps.
        """
        original_text = step_text.strip()

        # Find all time mentions in the step
        time_extractions = self._extract_all_times(original_text)

        if not time_extractions:
            # No times found - use prediction
            predicted_time = self.predictor.predict(original_text)
            return [ParsedStep(
                text=original_text,
                duration_minutes=predicted_time,
                original_text=original_text,
                confidence='predicted',
                time_phrases=[]
            )]

        # If only one time found, keep as single step
        if len(time_extractions) == 1:
            time_info = time_extractions[0]
            return [ParsedStep(
                text=original_text,
                duration_minutes=time_info['minutes'],
                original_text=original_text,
                confidence='extracted',
                time_phrases=[time_info['phrase']]
            )]

        # Multiple times found - split into separate steps
        return self._split_step_by_times(original_text, time_extractions)

    def _extract_all_times(self, text: str) -> List[Dict]:
        """Extract all time mentions from text"""
        extractions = []

        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                time_info = self._parse_time_match(match)
                if time_info:
                    extractions.append(time_info)

        # Remove duplicates and sort by position in text
        seen_phrases = set()
        unique_extractions = []
        for extraction in sorted(extractions, key=lambda x: x['start_pos']):
            if extraction['phrase'] not in seen_phrases:
                unique_extractions.append(extraction)
                seen_phrases.add(extraction['phrase'])

        return unique_extractions

    def _parse_time_match(self, match: re.Match) -> Optional[Dict]:
        """Parse a regex match into time information"""
        full_match = match.group(0)
        groups = match.groups()

        try:
            if len(groups) >= 2:
                # Handle range format (groups: start, end, unit)
                if len(groups) >= 3 and groups[1] and groups[1].replace('.', '').isdigit():
                    # Range format: "10-15 minutes"
                    start_time = float(groups[0])
                    end_time = float(groups[1])
                    unit = groups[2].lower()
                    avg_time = (start_time + end_time) / 2
                    minutes = avg_time * self.unit_conversions.get(unit, 1)
                else:
                    # Standard format: "10 minutes"
                    time_value = self._parse_time_value(groups[0])
                    unit = groups[1].lower()
                    minutes = time_value * self.unit_conversions.get(unit, 1)

                return {
                    'phrase': full_match,
                    'minutes': max(1, int(round(minutes))),  # At least 1 minute
                    'start_pos': match.start(),
                    'end_pos': match.end()
                }
        except (ValueError, IndexError):
            pass

        return None

    def _parse_time_value(self, time_str: str) -> float:
        """Parse time value handling fractions"""
        time_str = time_str.strip()

        # Handle fractions like "1/2", "1½", "1¼", "1¾"
        if '/' in time_str:
            parts = time_str.split('/')
            return float(parts[0]) / float(parts[1])
        elif '½' in time_str:
            base = time_str.replace('½', '')
            return (float(base) if base else 0) + 0.5
        elif '¼' in time_str:
            base = time_str.replace('¼', '')
            return (float(base) if base else 0) + 0.25
        elif '¾' in time_str:
            base = time_str.replace('¾', '')
            return (float(base) if base else 0) + 0.75
        else:
            return float(time_str)

    def _split_step_by_times(self, original_text: str, time_extractions: List[Dict]) -> List[ParsedStep]:
        """Split a step with multiple times into separate steps"""
        # Strategy: Try to intelligently break the step at logical points
        # For now, create substeps based on sentences or major phrases

        steps = []

        # If we have clear separators like "then", "next", "after", use those
        separators = ['then', 'next', 'after that', 'meanwhile', 'while', 'and then']

        # Simple approach: create one step per time mention
        for i, time_info in enumerate(time_extractions):
            step_text = f"Step {i + 1}: {time_info['phrase']} from original step"

            # Try to extract context around the time mention
            context_start = max(0, time_info['start_pos'] - 50)
            context_end = min(len(original_text), time_info['end_pos'] + 50)
            context = original_text[context_start:context_end].strip()

            # Clean up the context to make a reasonable step
            if context:
                step_text = context

            steps.append(ParsedStep(
                text=step_text,
                duration_minutes=time_info['minutes'],
                original_text=original_text,
                confidence='extracted',
                time_phrases=[time_info['phrase']]
            ))

        return steps

    def suggest_step_time(self, step_text: str) -> Dict:
        """Suggest a time for a step with confidence score"""
        # First try to extract
        extractions = self._extract_all_times(step_text)

        if extractions:
            return {
                'time_minutes': extractions[0]['minutes'],
                'confidence': 'high',
                'method': 'extracted',
                'phrases_found': [e['phrase'] for e in extractions]
            }

        # Use ML prediction
        predicted_time = self.predictor.predict(step_text)

        # Determine confidence based on keywords
        confidence = 'medium'
        high_confidence_keywords = ['mix', 'stir', 'add', 'combine', 'season']
        low_confidence_keywords = ['cook until done', 'bake until golden', 'simmer until tender']

        step_lower = step_text.lower()

        if any(keyword in step_lower for keyword in high_confidence_keywords):
            confidence = 'medium-high'
        elif any(keyword in step_lower for keyword in low_confidence_keywords):
            confidence = 'low'

        return {
            'time_minutes': predicted_time,
            'confidence': confidence,
            'method': 'predicted',
            'phrases_found': []
        }


# Integration helper functions
def process_recipe_steps(steps: List[str]) -> Tuple[List[str], List[int], List[str]]:
    """
    Process a list of recipe steps and return expanded steps, times, and confidence info.

    Returns:
        - expanded_steps: List of step texts (may be more than input if steps were split)
        - step_times: List of time durations in minutes
        - confidence_info: List of confidence indicators
    """
    parser = StepTimeParser()

    expanded_steps = []
    step_times = []
    confidence_info = []

    for original_step in steps:
        parsed_steps = parser.parse_step_times(original_step)

        for parsed_step in parsed_steps:
            expanded_steps.append(parsed_step.text)
            step_times.append(parsed_step.duration_minutes)
            confidence_info.append(parsed_step.confidence)

    return expanded_steps, step_times, confidence_info
