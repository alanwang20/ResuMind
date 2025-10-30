import logging
import json
import re
from typing import Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class ProofreadingQualityAgent:
    """
    Specialist Agent: Proofreading & Quality Assurance
    
    Mirrors Huntr's Proofreading AI that checks for:
    - Spelling and grammar errors
    - Formatting inconsistencies
    - Impact metrics validation (quantifiable achievements)
    - Repetitive or clichéd phrases
    - Resume length optimization
    """
    
    SYSTEM_PROMPT = """You are an expert resume proofreader and quality assurance specialist.

Your task is to meticulously review resume content for:
1. Spelling and grammar errors
2. Formatting inconsistencies (capitalization, punctuation, dates)
3. Impact metrics - flag achievements that lack quantifiable results
4. Repetitive phrases or overused buzzwords
5. Clichéd language that should be replaced with specific achievements
6. Resume length and content density

For each issue found, provide:
- The problematic text
- Why it's an issue
- A specific suggestion to fix it
- Severity level (critical, important, minor)

Output your analysis as a structured JSON object."""

    USER_PROMPT_TEMPLATE = """Review this resume content for quality issues:

**Target Role:** {role_title}

**Resume Content:**

**Professional Summary:**
{summary}

**Work Experience:**
{experience}

**Education:**
{education}

**Skills:**
{skills}

Analyze for:
1. Spelling/grammar errors
2. Missing metrics in achievements (flag bullets without numbers/percentages)
3. Repetitive words/phrases
4. Clichés like "team player", "hard worker", "fast learner"
5. Formatting inconsistencies
6. Content length (too long or too short sections)

{{
    "spelling_grammar": [
        {{
            "text": "The problematic text",
            "issue": "What's wrong",
            "suggestion": "How to fix it",
            "severity": "critical|important|minor"
        }}
    ],
    "missing_metrics": [
        {{
            "bullet": "Achievement bullet without quantifiable metrics",
            "issue": "No numbers/percentages/timeframes",
            "suggestion": "Add specific metrics like '30% improvement' or 'managed team of 5'",
            "severity": "important"
        }}
    ],
    "repetitive_phrases": [
        {{
            "phrase": "Word/phrase used too often",
            "count": 5,
            "suggestion": "Alternative wording",
            "severity": "minor"
        }}
    ],
    "cliches": [
        {{
            "text": "Clichéd phrase",
            "issue": "Overused buzzword",
            "suggestion": "Specific achievement-based replacement",
            "severity": "important"
        }}
    ],
    "formatting_issues": [
        {{
            "text": "Inconsistent formatting",
            "issue": "What's inconsistent",
            "suggestion": "How to standardize",
            "severity": "minor"
        }}
    ],
    "quality_score": {{
        "overall": 85,
        "spelling": 100,
        "metrics": 70,
        "formatting": 90,
        "content": 80
    }},
    "summary": "Brief overall assessment of resume quality"
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
    
    def review(self, resume_data: Dict, role_title: str) -> Dict:
        """
        Comprehensive quality review of resume content.
        
        Args:
            resume_data: Dict with summary, experience, education, skills
            role_title: Target role for context
        
        Returns:
            Dict with quality issues and suggestions
        """
        logger.info(f"Proofreading & Quality Agent reviewing resume for {role_title}")
        
        if self.use_openai:
            try:
                return self._review_with_openai(resume_data, role_title)
            except Exception as e:
                logger.error(f"OpenAI review failed: {e}, falling back to rules-based")
                return self._review_fallback(resume_data, role_title)
        else:
            return self._review_fallback(resume_data, role_title)
    
    def _review_with_openai(self, resume_data: Dict, role_title: str) -> Dict:
        """Use OpenAI for comprehensive quality review."""
        # Flatten experience list into text
        experience_text = "\n".join([
            f"{exp.get('title', '')} at {exp.get('company', '')} ({exp.get('dates', '')})\n" + 
            "\n".join(f"• {bullet}" for bullet in exp.get('bullets', []))
            for exp in resume_data.get('experience', [])
        ])
        
        # Flatten education list into text
        education_text = "\n".join([
            f"{edu.get('degree', '')} - {edu.get('school', '')} ({edu.get('year', '')})"
            for edu in resume_data.get('education', [])
        ])
        
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            role_title=role_title,
            summary=resume_data.get('summary', ''),
            experience=experience_text,
            education=education_text,
            skills=", ".join(resume_data.get('skills', []))
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        
        logger.info(f"Quality review complete: {result.get('quality_score', {}).get('overall', 0)}/100 score")
        return result
    
    def _review_fallback(self, resume_data: Dict, role_title: str) -> Dict:
        """Fallback rules-based quality review."""
        issues = {
            "spelling_grammar": [],
            "missing_metrics": [],
            "repetitive_phrases": [],
            "cliches": [],
            "formatting_issues": []
        }
        
        # Check for clichés
        cliche_phrases = [
            "team player", "hard worker", "fast learner", "detail-oriented",
            "self-motivated", "go-getter", "think outside the box", "synergy"
        ]
        
        all_text = " ".join([
            resume_data.get('summary', ''),
            " ".join([bullet for exp in resume_data.get('experience', []) 
                     for bullet in exp.get('bullets', [])])
        ]).lower()
        
        for cliche in cliche_phrases:
            if cliche in all_text:
                issues["cliches"].append({
                    "text": cliche,
                    "issue": "Overused buzzword",
                    "suggestion": "Replace with specific achievement",
                    "severity": "important"
                })
        
        # Check for missing metrics in experience bullets
        for exp in resume_data.get('experience', []):
            for bullet in exp.get('bullets', []):
                # Look for numbers, percentages, or quantifiers
                has_metrics = bool(re.search(r'\d+[%]?|\d+\+|(\d+,\d+)', bullet))
                if not has_metrics and len(bullet) > 20:
                    issues["missing_metrics"].append({
                        "bullet": bullet[:100] + "..." if len(bullet) > 100 else bullet,
                        "issue": "No quantifiable metrics",
                        "suggestion": "Add specific numbers, percentages, or timeframes",
                        "severity": "important"
                    })
        
        # Check for repetitive words
        words = all_text.split()
        word_freq = {}
        for word in words:
            if len(word) > 5:  # Only check longer words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        for word, count in word_freq.items():
            if count > 4:  # Used more than 4 times
                issues["repetitive_phrases"].append({
                    "phrase": word,
                    "count": count,
                    "suggestion": "Use synonyms for variety",
                    "severity": "minor"
                })
        
        # Calculate quality scores
        total_bullets = sum(len(exp.get('bullets', [])) for exp in resume_data.get('experience', []))
        bullets_with_metrics = total_bullets - len(issues["missing_metrics"])
        metrics_score = int((bullets_with_metrics / max(total_bullets, 1)) * 100)
        
        cliche_penalty = len(issues["cliches"]) * 5
        overall_score = max(0, 85 - cliche_penalty - (10 if metrics_score < 70 else 0))
        
        return {
            **issues,
            "quality_score": {
                "overall": overall_score,
                "spelling": 100,  # Can't check without spellcheck library
                "metrics": metrics_score,
                "formatting": 90,
                "content": 80
            },
            "summary": f"Resume has {len(issues['missing_metrics'])} bullets without metrics and "
                      f"{len(issues['cliches'])} clichéd phrases to address."
        }
