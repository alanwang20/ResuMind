import logging
import json
import re
from typing import Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class JobDescriptionAnalyzerAgent:
    """
    Specialist Agent: Job Description Analysis Pipeline
    
    Mirrors Huntr's extraction engine that parses job postings to extract:
    - Keywords (hard/soft skills, tech stack)
    - Responsibilities (semantic analysis)
    - Qualifications (education, certifications, experience levels)
    - Semantic understanding beyond simple keyword matching
    """
    
    SYSTEM_PROMPT = """You are an expert NLP-powered job description analyzer specializing in extracting structured data from job postings.

Your task is to perform deep analysis of job descriptions using both keyword extraction AND semantic understanding to identify:
1. Hard skills (technical skills, tools, languages, frameworks)
2. Soft skills (communication, leadership, collaboration)
3. Specific responsibilities (what the candidate will do)
4. Required qualifications (education, certifications, years of experience)
5. Preferred qualifications (nice-to-have items)
6. Contextual keywords (industry terms, company-specific terminology)

Use semantic analysis to understand meaning and context, not just exact word matches.
For example: "customer success" is semantically related to "client retention", "account management", etc.

Output your analysis as a structured JSON object."""

    USER_PROMPT_TEMPLATE = """Analyze this job posting with deep semantic understanding:

**Company:** {company_name}
**Role:** {role_title}

**Job Description:**
{job_description}

**Company Information:**
{company_info}

Extract and analyze the following with both keyword matching AND semantic understanding:

{{
    "keywords": {{
        "hard_skills": ["List of technical skills, tools, languages, frameworks - be specific"],
        "soft_skills": ["List of soft skills like leadership, communication, etc."],
        "industry_terms": ["Company/industry-specific terminology"],
        "tech_stack": ["Specific technologies mentioned"]
    }},
    "responsibilities": [
        {{
            "description": "What the candidate will do (extracted from JD)",
            "keywords": ["Key terms from this responsibility"],
            "semantic_matches": ["Related terms/skills that match semantically"]
        }}
    ],
    "qualifications": {{
        "required": {{
            "education": ["Required degrees/education"],
            "certifications": ["Required certifications"],
            "experience_years": "Minimum years required",
            "must_have_skills": ["Absolutely required skills"]
        }},
        "preferred": {{
            "education": ["Preferred degrees/education"],
            "certifications": ["Preferred certifications"],
            "nice_to_have_skills": ["Preferred but not required skills"]
        }}
    }},
    "seniority_level": "junior|mid|senior|executive",
    "semantic_context": {{
        "role_focus": "Primary focus of role (e.g., backend development, data analysis, etc.)",
        "key_outcomes": ["What success looks like in this role"],
        "related_roles": ["Similar job titles that would have relevant experience"]
    }}
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
        Deep analysis of job description to extract structured data.
        
        Args:
            role_data: Dict with company_name, role_title, job_description, company_info
        
        Returns:
            Dict with keywords, responsibilities, qualifications, semantic context
        """
        logger.info(f"Job Description Analyzer processing: {role_data['role_title']} at {role_data['company_name']}")
        
        if self.use_openai:
            try:
                return self._analyze_with_openai(role_data)
            except Exception as e:
                logger.error(f"OpenAI analysis failed: {e}, falling back to rules-based extraction")
                return self._analyze_fallback(role_data)
        else:
            return self._analyze_fallback(role_data)
    
    def _analyze_with_openai(self, role_data: Dict) -> Dict:
        """Use OpenAI for semantic analysis and extraction."""
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
        
        logger.info(f"Extracted {len(result.get('keywords', {}).get('hard_skills', []))} hard skills, "
                   f"{len(result.get('responsibilities', []))} responsibilities")
        return result
    
    def _analyze_fallback(self, role_data: Dict) -> Dict:
        """Fallback rules-based extraction with semantic keyword grouping."""
        jd = role_data['job_description'].lower()
        role_title = role_data['role_title'].lower()
        
        # Extract technical skills
        tech_patterns = [
            r'\b(python|java|javascript|typescript|react|node\.?js|angular|vue|sql|nosql|aws|azure|gcp|docker|kubernetes|git)\b',
            r'\b(machine learning|deep learning|ai|nlp|computer vision|data science|analytics)\b',
            r'\b(api|rest|graphql|microservices|devops|ci/cd|agile|scrum)\b'
        ]
        
        hard_skills = set()
        for pattern in tech_patterns:
            hard_skills.update(re.findall(pattern, jd))
        
        # Extract soft skills
        soft_skill_keywords = ['leadership', 'communication', 'collaboration', 'teamwork', 
                              'problem-solving', 'analytical', 'creative', 'organized']
        soft_skills = [skill for skill in soft_skill_keywords if skill in jd]
        
        # Extract responsibilities (look for bullet points or sentences with action verbs)
        responsibility_verbs = ['develop', 'design', 'implement', 'manage', 'lead', 'collaborate',
                               'build', 'create', 'analyze', 'optimize', 'maintain']
        responsibilities = []
        for verb in responsibility_verbs:
            pattern = rf'([^.]*{verb}[^.]*\.)'
            matches = re.findall(pattern, jd)
            for match in matches[:3]:  # Limit to 3 per verb
                responsibilities.append({
                    "description": match.strip(),
                    "keywords": [verb],
                    "semantic_matches": []
                })
        
        # Determine seniority level
        seniority = 'mid'
        if any(word in role_title for word in ['senior', 'lead', 'principal', 'staff']):
            seniority = 'senior'
        elif any(word in role_title for word in ['junior', 'entry', 'associate']):
            seniority = 'junior'
        elif any(word in role_title for word in ['director', 'vp', 'head', 'chief']):
            seniority = 'executive'
        
        # Extract years of experience
        years_match = re.search(r'(\d+)\+?\s*years?', jd)
        experience_years = years_match.group(1) if years_match else "2-5"
        
        return {
            "keywords": {
                "hard_skills": list(hard_skills),
                "soft_skills": soft_skills,
                "industry_terms": [],
                "tech_stack": list(hard_skills)
            },
            "responsibilities": responsibilities[:10],  # Limit to 10
            "qualifications": {
                "required": {
                    "education": ["Bachelor's degree"],
                    "certifications": [],
                    "experience_years": experience_years,
                    "must_have_skills": list(hard_skills)[:5]
                },
                "preferred": {
                    "education": ["Master's degree"],
                    "certifications": [],
                    "nice_to_have_skills": list(hard_skills)[5:10]
                }
            },
            "seniority_level": seniority,
            "semantic_context": {
                "role_focus": role_title,
                "key_outcomes": ["Deliver high-quality solutions", "Meet project deadlines"],
                "related_roles": []
            }
        }
