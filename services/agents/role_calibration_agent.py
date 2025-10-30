import logging
import json
from typing import Dict
from openai import OpenAI

logger = logging.getLogger(__name__)


class RoleCalibrationAgent:
    """
    Specialist Agent: Role-Specific Calibration
    
    Mirrors Huntr's Role-Alignment AI that:
    - Adjusts tone based on seniority level (junior/mid/senior/executive)
    - Calibrates vocabulary and leadership cues
    - Modulates formality and writing style
    - Ensures resume reads authentically for the target level
    """
    
    SYSTEM_PROMPT = """You are an expert resume calibration specialist who adjusts resume tone and language based on career level.

Your task is to calibrate resume content for the appropriate seniority level:

**Junior Level (0-2 years):**
- Focus on learning, growth, collaboration
- Emphasize: "Assisted", "Supported", "Contributed to"
- Highlight: coursework, projects, internships, eagerness to learn
- Tone: Enthusiastic, collaborative, growth-oriented

**Mid Level (3-7 years):**
- Focus on ownership, execution, results
- Emphasize: "Developed", "Implemented", "Delivered", "Improved"
- Highlight: independent projects, measurable impact, technical depth
- Tone: Confident, results-driven, technically competent

**Senior Level (8-12 years):**
- Focus on leadership, strategy, mentorship
- Emphasize: "Led", "Architected", "Drove", "Mentored", "Optimized"
- Highlight: system design, team leadership, business impact
- Tone: Strategic, authoritative, impact-focused

**Executive Level (13+ years):**
- Focus on vision, transformation, organizational impact
- Emphasize: "Directed", "Transformed", "Established", "Spearheaded"
- Highlight: P&L responsibility, org changes, strategic initiatives
- Tone: Visionary, commanding, business-outcome focused

For each resume section, suggest tone adjustments and vocabulary changes appropriate for the target level.

Output your calibration suggestions as a structured JSON object."""

    USER_PROMPT_TEMPLATE = """Calibrate this resume content for the appropriate seniority level:

**Target Role:** {role_title}
**Target Seniority:** {seniority_level}

**Current Resume Content:**

**Summary:**
{summary}

**Experience Bullets:**
{experience_bullets}

**Tone Analysis Instructions:**
1. Assess if current language matches target seniority level
2. Identify words/phrases that feel too junior or too senior
3. Suggest vocabulary replacements appropriate for level
4. Adjust leadership cues and formality
5. Ensure authenticity - don't inflate accomplishments

{{
    "tone_assessment": {{
        "current_level": "junior|mid|senior|executive",
        "target_level": "{seniority_level}",
        "alignment_score": 75,
        "issues": [
            "Language too junior/senior for target role",
            "Missing leadership indicators",
            "Overly formal/casual tone"
        ]
    }},
    "vocabulary_adjustments": [
        {{
            "section": "summary|bullet",
            "original_phrase": "Current wording",
            "calibrated_phrase": "Level-appropriate wording",
            "reason": "Why this better fits {seniority_level} level",
            "example": "How to use this in context"
        }}
    ],
    "leadership_calibration": {{
        "current_leadership_cues": ["List leadership indicators in current resume"],
        "suggested_additions": ["Leadership phrases to add for {seniority_level} level"],
        "tone_shift": "Description of how to shift tone"
    }},
    "formality_adjustments": {{
        "current_formality": "too_casual|appropriate|too_formal",
        "target_formality": "Level-appropriate formality",
        "suggestions": ["How to adjust formality level"]
    }},
    "calibrated_examples": [
        {{
            "original": "Original bullet/summary",
            "calibrated": "Fully calibrated version for {seniority_level} level",
            "key_changes": ["What changed and why"]
        }}
    ]
}}

Return ONLY the JSON object, no additional text."""

    def __init__(self, use_openai: bool = True):
        self.use_openai = use_openai
        if use_openai:
            try:
                self.client = OpenAI()
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.use_openai = False
    
    def calibrate(self, resume_data: Dict, seniority_level: str, role_title: str) -> Dict:
        """
        Calibrate resume tone for appropriate seniority level.
        
        Args:
            resume_data: Dict with summary, experience
            seniority_level: junior, mid, senior, or executive
            role_title: Target role for context
        
        Returns:
            Dict with tone adjustments and calibrated examples
        """
        logger.info(f"Role Calibration Agent adjusting for {seniority_level} level")
        
        if self.use_openai:
            try:
                return self._calibrate_with_openai(resume_data, seniority_level, role_title)
            except Exception as e:
                logger.error(f"OpenAI calibration failed: {e}, falling back to rules-based")
                return self._calibrate_fallback(resume_data, seniority_level, role_title)
        else:
            return self._calibrate_fallback(resume_data, seniority_level, role_title)
    
    def _calibrate_with_openai(self, resume_data: Dict, seniority_level: str, role_title: str) -> Dict:
        """Use OpenAI for intelligent tone calibration."""
        # Flatten experience bullets
        experience_bullets = []
        for exp in resume_data.get('experience', []):
            for bullet in exp.get('bullets', []):
                experience_bullets.append(bullet)
        
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            role_title=role_title,
            seniority_level=seniority_level,
            summary=resume_data.get('summary', ''),
            experience_bullets="\n".join(experience_bullets[:10])
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        
        logger.info(f"Tone calibrated for {seniority_level} level: "
                   f"{result.get('tone_assessment', {}).get('alignment_score', 0)}% aligned")
        return result
    
    def _calibrate_fallback(self, resume_data: Dict, seniority_level: str, role_title: str) -> Dict:
        """Fallback rules-based tone calibration."""
        # Define action verbs by level
        level_verbs = {
            "junior": ["assisted", "supported", "contributed", "learned", "participated", "helped"],
            "mid": ["developed", "implemented", "delivered", "improved", "built", "created"],
            "senior": ["led", "architected", "drove", "mentored", "optimized", "designed"],
            "executive": ["directed", "transformed", "established", "spearheaded", "envisioned", "pioneered"]
        }
        
        current_text = " ".join([
            resume_data.get('summary', ''),
            " ".join([bullet for exp in resume_data.get('experience', []) 
                     for bullet in exp.get('bullets', [])])
        ]).lower()
        
        # Detect current level based on verb usage
        current_level = "mid"
        for level, verbs in level_verbs.items():
            if sum(verb in current_text for verb in verbs) >= 2:
                current_level = level
                break
        
        # Alignment score
        alignment_score = 100 if current_level == seniority_level else 60
        
        # Suggestions
        target_verbs = level_verbs.get(seniority_level, level_verbs["mid"])
        
        return {
            "tone_assessment": {
                "current_level": current_level,
                "target_level": seniority_level,
                "alignment_score": alignment_score,
                "issues": [] if current_level == seniority_level else [
                    f"Language reads as {current_level} level, should be {seniority_level}"
                ]
            },
            "vocabulary_adjustments": [
                {
                    "section": "bullets",
                    "original_phrase": "Worked on",
                    "calibrated_phrase": target_verbs[0].capitalize(),
                    "reason": f"'{target_verbs[0]}' is more appropriate for {seniority_level} level",
                    "example": f"{target_verbs[0].capitalize()} a new feature that improved performance by 25%"
                }
            ],
            "leadership_calibration": {
                "current_leadership_cues": [],
                "suggested_additions": [f"Use verbs like: {', '.join(target_verbs)}"],
                "tone_shift": f"Shift from collaborative to ownership" if seniority_level in ["mid", "senior"] else "Focus on strategic impact"
            },
            "formality_adjustments": {
                "current_formality": "appropriate",
                "target_formality": "professional",
                "suggestions": []
            },
            "calibrated_examples": []
        }
