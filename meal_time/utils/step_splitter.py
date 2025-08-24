# meal_time/utils/step_splitter.py
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SplitStep:
    """Represents a single step with its associated time"""
    instruction: str
    time_minutes: Optional[int] = None
    time_text: Optional[str] = None


class StepSplitter:
    """Utility class for splitting recipe steps containing multiple time instructions"""
    
    # Regex patterns for detecting time expressions
    TIME_PATTERNS = [
        # Range patterns first: "10-15 minutes", "1-2 hours"  
        r'(\d+)\s*[-–]\s*(\d+)\s*(minutes|minute|mins|min|hours|hour|hrs|hr)',
        
        # Approximate patterns: "about 10 minutes", "around 30 mins"
        r'(about|around|approximately|roughly)\s+(\d+(?:\.\d+)?)\s*(minutes|minute|mins|min|hours|hour|hrs|hr)',
        
        # Compound patterns: "1 hour 30 minutes", "2 hrs 15 mins"
        r'(\d+(?:\.\d+)?)\s*(hours|hour|hrs|hr)\s+(\d+)\s*(minutes|minute|mins|min)',
        
        # Hours with optional minutes: "1 hour", "2 hours and 30 minutes"
        r'(?<!\-)(\d+(?:\.\d+)?)\s*(hours|hour|hrs|hr)\s*(?:and\s*)?(?:(\d+)\s*(minutes|minute|mins|min))?',
        
        # Standard patterns: "10 minutes", "30 mins", etc. (avoid negative numbers)
        r'(?<!\-)(\d+(?:\.\d+)?)\s*(minutes|minute|mins|min)',
        r'(?<!\-)(\d+(?:\.\d+)?)\s*(seconds|second|secs|sec)',
    ]
    
    # Conjunctions that indicate step transitions
    SPLIT_CONJUNCTIONS = [
        r'\bthen\b',
        r'\band\s+then\b', 
        r'\bnext\b',
        r'\bafter\s+(?:that|this)\b',
        r'\bfollowed\s+by\b',
        r'\bonce\s+(?:done|finished|complete)\b',
        r'\bwhen\s+(?:done|finished|complete)\b',
        r'\bimmediately\s+(?:after|before)\b',
        r'\bmeanwhile\b',
        r'\bat\s+the\s+same\s+time\b',
        r'\bwhile\s+(?:that|this|it)(?:\s+is)?\s+(?:cooking|baking|simmering)\b',
        r'\band\s+(?:serve|remove|add|season|garnish|cool|let|allow)\b',  # "and serve", "and remove", etc.
        # Punctuation-based splits
        r'[.;]\s*',
    ]
    
    @classmethod
    def extract_time_from_text(cls, text: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Extract time value from text and return (minutes, original_text)
        Returns (None, None) if no time found
        """
        text_lower = text.lower().strip()
        
        for pattern in cls.TIME_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                time_minutes = 0
                time_text = match.group(0)
                
                # Handle range patterns first (they have specific structure)
                if '-' in time_text or '–' in time_text:
                    start = int(groups[0])
                    end = int(groups[1])
                    unit = groups[2].lower()
                    avg_time = (start + end) / 2  # Use regular division for proper average
                    if 'hour' in unit or 'hr' in unit:
                        time_minutes = int(avg_time * 60)
                    else:
                        time_minutes = int(avg_time)
                    return time_minutes, time_text
                
                # Handle approximate patterns
                elif 'about|around|approximately|roughly' in pattern:
                    qualifier = groups[0]
                    time_value = float(groups[1])
                    unit = groups[2].lower()
                    if 'hour' in unit:
                        time_minutes = int(time_value * 60)
                    elif 'minute' in unit:
                        time_minutes = int(time_value)
                    elif 'second' in unit:
                        time_minutes = max(1, int(time_value // 60))
                    return time_minutes, time_text
                
                # Handle compound hour+minute patterns
                elif len(groups) >= 4 and groups[2] and 'hour' in groups[1]:
                    hours = float(groups[0])
                    minutes = float(groups[2])
                    time_minutes = int(hours * 60 + minutes)
                    return time_minutes, time_text
                
                # Handle minute patterns
                elif 'minute' in groups[1].lower() or 'min' in groups[1].lower():
                    time_minutes = int(float(groups[0]))
                    return time_minutes, time_text
                
                # Handle hour patterns
                elif 'hour' in groups[1].lower() or 'hr' in groups[1].lower():
                    hours = float(groups[0])
                    minutes = float(groups[2]) if len(groups) > 2 and groups[2] else 0
                    time_minutes = int(hours * 60 + minutes)
                    return time_minutes, time_text
                
                # Handle second patterns
                elif 'second' in groups[1].lower() or 'sec' in groups[1].lower():
                    seconds = int(float(groups[0]))
                    time_minutes = max(1, seconds // 60)
                    return time_minutes, time_text
        
        return None, None
    
    @classmethod
    def has_multiple_time_instructions(cls, step_text: str) -> bool:
        """Check if a step contains multiple time instructions"""
        time_count = 0
        conjunction_found = False
        
        # Count time patterns
        for pattern in cls.TIME_PATTERNS:
            matches = re.findall(pattern, step_text.lower())
            time_count += len(matches)
        
        # Check for conjunctions
        for conjunction in cls.SPLIT_CONJUNCTIONS:
            if re.search(conjunction, step_text.lower()):
                conjunction_found = True
                break
        
        # Consider it splittable if there are multiple times OR a conjunction with at least one time
        return time_count > 1 or (time_count >= 1 and conjunction_found)
    
    @classmethod
    def split_step(cls, step_text: str) -> List[SplitStep]:
        """
        Split a step text into multiple steps if it contains multiple time instructions
        Returns list of SplitStep objects
        """
        # Clean the input
        step_text = step_text.strip()
        
        if not cls.has_multiple_time_instructions(step_text):
            # No splitting needed, return as single step
            time_minutes, time_text = cls.extract_time_from_text(step_text)
            return [SplitStep(
                instruction=step_text,
                time_minutes=time_minutes,
                time_text=time_text
            )]
        
        # Try to split by conjunctions
        parts = []
        remaining_text = step_text
        
        # Split by conjunctions, preserving the conjunction context
        for conjunction in cls.SPLIT_CONJUNCTIONS:
            if re.search(conjunction, remaining_text, re.IGNORECASE):
                # Split and keep meaningful parts
                split_parts = re.split(f'({conjunction})', remaining_text, flags=re.IGNORECASE)
                
                # Reconstruct meaningful parts
                current_part = ""
                for i, part in enumerate(split_parts):
                    if re.match(conjunction, part.strip(), re.IGNORECASE):
                        # This is a conjunction, finish current part if it has content
                        if current_part.strip():
                            parts.append(current_part.strip())
                            current_part = ""
                    else:
                        current_part += part
                
                # Add remaining part if any
                if current_part.strip():
                    parts.append(current_part.strip())
                break
        
        # If no conjunction splits worked, try to split by sentences or time patterns
        if not parts:
            # Split by periods or semicolons
            sentence_parts = re.split(r'[.;]\s*', step_text)
            parts = [part.strip() for part in sentence_parts if part.strip()]
        
        # If still no parts, split by commas as last resort
        if len(parts) <= 1:
            comma_parts = re.split(r',\s*(?=\w+\s+for\s+\d+)', step_text)
            parts = [part.strip() for part in comma_parts if part.strip()]
        
        # If still only one part, return as is
        if len(parts) <= 1:
            time_minutes, time_text = cls.extract_time_from_text(step_text)
            return [SplitStep(
                instruction=step_text,
                time_minutes=time_minutes,
                time_text=time_text
            )]
        
        # Process each part to extract time and clean instruction
        split_steps = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            time_minutes, time_text = cls.extract_time_from_text(part)
            
            # Clean up the instruction text
            instruction = cls._clean_instruction_text(part, time_text)
            
            # Only add if instruction has meaningful content
            if len(instruction.strip()) > 3:  # At least a few characters
                split_steps.append(SplitStep(
                    instruction=instruction,
                    time_minutes=time_minutes,
                    time_text=time_text
                ))
        
        # If no valid split steps, return original
        if not split_steps:
            time_minutes, time_text = cls.extract_time_from_text(step_text)
            return [SplitStep(
                instruction=step_text,
                time_minutes=time_minutes,
                time_text=time_text
            )]
        
        return split_steps
    
    @classmethod
    def _clean_instruction_text(cls, text: str, time_text: Optional[str]) -> str:
        """Clean up instruction text by ensuring proper capitalization and punctuation"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove leading conjunctions that might be left over
        text = re.sub(r'^(then|and then|next|after that|followed by)\s+', '', text, flags=re.IGNORECASE)
        
        # Remove trailing punctuation from splitting (like ",.") and replace with single period
        text = re.sub(r'[,;]\s*\.\s*$', '.', text)
        text = re.sub(r'[,;]\s*$', '.', text)
        
        # Capitalize first letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        # Ensure it ends with a period if it doesn't already end with punctuation
        if text and text[-1] not in '.!?':
            text += '.'
        
        return text
    
    @classmethod
    def split_recipe_steps(cls, steps: List[str]) -> Tuple[List[str], List[int]]:
        """
        Split all steps in a recipe and return new steps and step_times lists
        Returns (new_steps, new_step_times)
        """
        new_steps = []
        new_step_times = []
        
        for step in steps:
            split_steps = cls.split_step(step)
            
            for split_step in split_steps:
                new_steps.append(split_step.instruction)
                # Use extracted time or fallback to 5 minutes
                time_minutes = split_step.time_minutes if split_step.time_minutes is not None else 5
                new_step_times.append(time_minutes)
        
        return new_steps, new_step_times