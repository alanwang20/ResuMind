import logging
import json
from typing import Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class ContentOptimizerAgent:
    """
    Specialist Agent: Content Optimization & Rewriting
    
    Mirrors Huntr's Content Rewriter that:
    - Rewrites professional summaries with job-aligned intros
    - Enhances bullet points with keyword-infused achievements
    - Prioritizes skills section by relevance to job posting
    - Integrates extracted keywords naturally into content
    """
    
    SYSTEM_PROMPT = """You are an expert resume content optimizer specializing in rewriting resume sections to align with specific job postings.

Your task is to:
1. Rewrite professional summaries to align with target role and incorporate key qualifications
2. Enhance achievement bullets to integrate relevant keywords while maintaining authenticity
3. Prioritize and reorder skills based on job posting relevance
4. Ensure all rewrites are:
   - Truthful to the original content (don't fabricate experience)
   - Natural and readable (not keyword-stuffed)
   - Quantifiable where possible (include metrics)
   - ATS-friendly (clear, scannable format)

For each rewrite, provide the original text and optimized version with explanation.

Output your optimizations as a structured JSON object."""

    USER_PROMPT_TEMPLATE = """Optimize this resume content for the target role:

**Target Role:** {role_title}
**Target Company:** {company_name}

**Job Requirements (Keywords to Integrate):**
Hard Skills: {hard_skills}
Soft Skills: {soft_skills}
Key Responsibilities: {responsibilities}

**Current Resume Content:**

**Summary:**
{current_summary}

**Experience Bullets:**
{experience_bullets}

**Skills:**
{current_skills}

**Optimization Instructions:**
1. Rewrite the summary to highlight qualifications matching the job requirements
2. Enhance 3-5 key experience bullets to naturally integrate relevant keywords
3. Prioritize skills list by relevance to this specific job posting
4. Keep all content truthful - don't add fake experience or metrics

{{
    "optimized_summary": {{
        "original": "Current summary text",
        "optimized": "Rewritten summary integrating keywords",
        "explanation": "Why these changes align with the job",
        "keywords_integrated": ["List of keywords naturally added"]
    }},
    "optimized_bullets": [
        {{
            "original": "Original bullet point",
            "optimized": "Enhanced bullet with keywords",
            "explanation": "How this better matches job requirements",
            "keywords_integrated": ["Keywords added"],
            "impact_score": 85
        }}
    ],
    "optimized_skills": {{
        "prioritized_skills": ["Skills ordered by relevance to job"],
        "skills_to_add": ["Relevant skills from JD the user might have"],
        "skills_to_emphasize": ["Skills to highlight prominently"],
        "explanation": "Why this ordering matches the job posting"
    }},
    "overall_suggestions": [
        "Additional recommendations for resume improvement"
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
    
    def optimize(self, resume_data: Dict, job_analysis: Dict, role_data: Dict) -> Dict:
        """
        Optimize resume content to align with job posting.
        
        Args:
            resume_data: Dict with summary, experience, skills
            job_analysis: Output from JobDescriptionAnalyzerAgent
            role_data: Dict with company_name, role_title
        
        Returns:
            Dict with optimized content and suggestions
        """
        logger.info(f"Content Optimizer optimizing resume for {role_data['role_title']}")
        
        if self.use_openai:
            try:
                return self._optimize_with_openai(resume_data, job_analysis, role_data)
            except Exception as e:
                logger.error(f"OpenAI optimization failed: {e}, falling back to rules-based")
                return self._optimize_fallback(resume_data, job_analysis, role_data)
        else:
            return self._optimize_fallback(resume_data, job_analysis, role_data)
    
    def _optimize_with_openai(self, resume_data: Dict, job_analysis: Dict, role_data: Dict) -> Dict:
        """Use OpenAI for intelligent content optimization."""
        # Extract keywords from job analysis
        keywords = job_analysis.get('keywords', {})
        hard_skills = keywords.get('hard_skills', [])
        soft_skills = keywords.get('soft_skills', [])
        responsibilities = [r.get('description', '') for r in job_analysis.get('responsibilities', [])]
        
        # Flatten experience bullets
        experience_bullets = []
        for exp in resume_data.get('experience', []):
            for bullet in exp.get('bullets', []):
                experience_bullets.append(f"{exp.get('title', 'Role')} at {exp.get('company', 'Company')}: {bullet}")
        
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            role_title=role_data['role_title'],
            company_name=role_data['company_name'],
            hard_skills=", ".join(hard_skills[:15]),
            soft_skills=", ".join(soft_skills[:10]),
            responsibilities="; ".join(responsibilities[:5]),
            current_summary=resume_data.get('summary', ''),
            experience_bullets="\n".join(experience_bullets[:10]),
            current_skills=", ".join(resume_data.get('skills', []))
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
        
        logger.info(f"Content optimized: {len(result.get('optimized_bullets', []))} bullets enhanced")
        return result
    
    def _optimize_fallback(self, resume_data: Dict, job_analysis: Dict, role_data: Dict) -> Dict:
        """Fallback rules-based optimization."""
        keywords = job_analysis.get('keywords', {})
        hard_skills = keywords.get('hard_skills', [])
        soft_skills = keywords.get('soft_skills', [])
        
        current_summary = resume_data.get('summary', '')
        current_skills = resume_data.get('skills', [])
        
        # Optimize summary by adding top keywords
        optimized_summary_text = current_summary
        if current_summary:
            # Add top 3 hard skills if not present
            for skill in hard_skills[:3]:
                if skill.lower() not in current_summary.lower():
                    optimized_summary_text = f"{current_summary} Experienced with {skill}."
                    break
        
        # Prioritize skills by matching with job requirements
        matched_skills = []
        unmatched_skills = []
        
        for skill in current_skills:
            skill_lower = skill.lower()
            if any(hs.lower() in skill_lower or skill_lower in hs.lower() for hs in hard_skills):
                matched_skills.append(skill)
            else:
                unmatched_skills.append(skill)
        
        prioritized_skills = matched_skills + unmatched_skills
        
        # Suggest skills to add from job description
        skills_to_add = [hs for hs in hard_skills 
                        if not any(hs.lower() in s.lower() for s in current_skills)][:5]
        
        return {
            "optimized_summary": {
                "original": current_summary,
                "optimized": optimized_summary_text,
                "explanation": f"Integrated top job requirements into summary",
                "keywords_integrated": hard_skills[:3]
            },
            "optimized_bullets": [],  # Would need more complex logic
            "optimized_skills": {
                "prioritized_skills": prioritized_skills,
                "skills_to_add": skills_to_add,
                "skills_to_emphasize": matched_skills[:5],
                "explanation": f"Prioritized {len(matched_skills)} skills matching job requirements"
            },
            "overall_suggestions": [
                f"Add these relevant skills from job posting: {', '.join(skills_to_add[:3])}",
                f"Emphasize {', '.join(matched_skills[:3])} in your experience bullets"
            ]
        }
