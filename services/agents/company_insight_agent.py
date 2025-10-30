import logging
import json
from typing import Dict
from openai import OpenAI

logger = logging.getLogger(__name__)


class CompanyInsightAgent:
    """
    Agent 1: Analyzes company and job posting to understand:
    - Company-specific resume preferences (e.g., big tech wants 1-2 word bullet points)
    - Key requirements and keywords
    - Tone and formatting expectations
    """
    
    SYSTEM_PROMPT = """You are an expert recruiter and resume analyst specializing in understanding company-specific resume preferences and requirements.

Your task is to analyze job postings and company information to extract:
1. Company-specific resume formatting preferences (e.g., bullet point style, length, structure)
2. Key requirements and must-have qualifications
3. Important keywords and terminology used by the company
4. Preferred tone and communication style
5. Industry-specific expectations

Output your analysis as a structured JSON object."""

    USER_PROMPT_TEMPLATE = """Analyze the following job posting and company information:

**Company:** {company_name}
**Role:** {role_title}

**Job Description:**
{job_description}

**Company Information:**
{company_info}

Please provide a detailed analysis with the following structure:
{{
    "company_preferences": {{
        "resume_format": "Description of preferred resume format and structure",
        "bullet_style": "Preferred bullet point style (e.g., concise 1-2 word starts, detailed paragraphs, etc.)",
        "length_preference": "Preferred resume length",
        "tone": "Preferred communication tone"
    }},
    "key_requirements": [
        "List of must-have qualifications and requirements"
    ],
    "important_keywords": [
        "List of 15-20 most important keywords from the job posting"
    ],
    "skill_priorities": [
        "Ordered list of skill categories by importance"
    ],
    "company_values": [
        "Key company values or cultural indicators from the posting"
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
    
    def analyze(self, role_data: Dict) -> Dict:
        """
        Analyze company and role to extract insights.
        
        Args:
            role_data: Dict with company_name, role_title, job_description, company_info
        
        Returns:
            Dict with company_preferences, key_requirements, important_keywords, etc.
        """
        logger.info(f"Company Insight Agent analyzing role: {role_data['role_title']} at {role_data['company_name']}")
        
        if self.use_openai:
            try:
                return self._analyze_with_openai(role_data)
            except Exception as e:
                logger.error(f"OpenAI analysis failed: {e}, falling back to rules-based")
                return self._analyze_fallback(role_data)
        else:
            return self._analyze_fallback(role_data)
    
    def _analyze_with_openai(self, role_data: Dict) -> Dict:
        """Use OpenAI to analyze company preferences."""
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            company_name=role_data['company_name'],
            role_title=role_data['role_title'],
            job_description=role_data['job_description'],
            company_info=role_data.get('company_info', 'No additional company information provided.')
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
        
        logger.info(f"Company insights extracted: {len(result.get('important_keywords', []))} keywords identified")
        return result
    
    def _analyze_fallback(self, role_data: Dict) -> Dict:
        """Fallback rules-based analysis."""
        from utils import top_ngrams, clean_text
        
        jd = role_data['job_description']
        keywords = top_ngrams(jd, top_k=20)
        
        is_big_tech = any(company in role_data['company_name'].lower() 
                         for company in ['google', 'meta', 'facebook', 'amazon', 'microsoft', 'apple', 'netflix'])
        
        return {
            "company_preferences": {
                "resume_format": "One-page, reverse chronological" if is_big_tech else "Concise, skills-focused",
                "bullet_style": "1-2 word action verb starts with quantified results" if is_big_tech else "Clear, achievement-focused bullets",
                "length_preference": "One page strongly preferred" if is_big_tech else "1-2 pages",
                "tone": "Direct, data-driven" if is_big_tech else "Professional, accomplishment-focused"
            },
            "key_requirements": [kw for kw, _ in keywords[:10]],
            "important_keywords": [kw for kw, _ in keywords],
            "skill_priorities": list(set([kw.split()[0] for kw, _ in keywords[:15] if ' ' not in kw])),
            "company_values": ["innovation", "impact", "collaboration"]
        }
