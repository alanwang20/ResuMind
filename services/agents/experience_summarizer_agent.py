import logging
import json
from typing import Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class ExperienceSummarizerAgent:
    """
    Agent 2: Summarizes user profile into structured accomplishment summaries.
    Converts raw profile data into clean, impactful summaries with metrics.
    """
    
    SYSTEM_PROMPT = """You are an expert resume writer who excels at transforming raw experience data into compelling, achievement-focused summaries.

Your task is to:
1. Extract key accomplishments from each experience/project
2. Quantify impact wherever possible
3. Use strong action verbs
4. Highlight transferable skills
5. Create concise, impactful summaries

Output your summaries as a structured JSON object."""

    USER_PROMPT_TEMPLATE = """Summarize the following user profile into structured accomplishment summaries:

**User Information:**
Name: {name}
Summary: {summary}

**Education:**
{education}

**Work Experiences:**
{experiences}

**Projects:**
{projects}

**Skills:**
{skills}

Please create structured summaries for each experience and project that:
- Start with strong action verbs
- Include quantifiable metrics where available
- Highlight key technologies and skills
- Focus on impact and results

Return a JSON object with this structure:
{{
    "experience_summaries": [
        {{
            "title": "Job title",
            "company": "Company name",
            "period": "Date range",
            "bullets": [
                "Achievement-focused bullet points"
            ],
            "key_skills": ["skill1", "skill2"],
            "impact_areas": ["area1", "area2"]
        }}
    ],
    "project_summaries": [
        {{
            "name": "Project name",
            "bullets": [
                "Achievement-focused descriptions"
            ],
            "technologies": ["tech1", "tech2"],
            "impact_areas": ["area1"]
        }}
    ],
    "skill_summary": {{
        "technical": ["skill1", "skill2"],
        "soft": ["skill1", "skill2"],
        "domain": ["skill1", "skill2"]
    }},
    "education_summary": [
        {{
            "degree": "Degree",
            "institution": "School",
            "highlights": ["highlight1", "highlight2"]
        }}
    ]
}}

Return ONLY the JSON object."""

    def __init__(self, use_openai: bool = True):
        self.use_openai = use_openai
        if use_openai:
            try:
                self.client = OpenAI()
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.use_openai = False
    
    def summarize(self, profile_data: Dict) -> Dict:
        """
        Summarize user profile into structured accomplishments.
        
        Args:
            profile_data: Complete user profile dict from database
        
        Returns:
            Dict with experience_summaries, project_summaries, skill_summary, etc.
        """
        logger.info(f"Experience Summarizer Agent processing profile for: {profile_data.get('name', 'Unknown')}")
        
        if self.use_openai:
            try:
                return self._summarize_with_openai(profile_data)
            except Exception as e:
                logger.error(f"OpenAI summarization failed: {e}, falling back to rules-based")
                return self._summarize_fallback(profile_data)
        else:
            return self._summarize_fallback(profile_data)
    
    def _summarize_with_openai(self, profile_data: Dict) -> Dict:
        """Use OpenAI to create summaries."""
        education_text = "\n".join([
            f"- {e['degree']} in {e.get('field_of_study', 'N/A')} from {e['institution']} ({e.get('start_date', '')}-{e.get('end_date', '')})"
            for e in profile_data.get('education', [])
        ]) or "No education information provided"
        
        experiences_text = "\n\n".join([
            f"**{e['title']} at {e['company']}** ({e.get('start_date', '')}-{e.get('end_date', 'Present' if e.get('current') else '')})\n{e.get('description', '')}\nAchievements: {e.get('achievements', 'N/A')}"
            for e in profile_data.get('experiences', [])
        ]) or "No work experience provided"
        
        projects_text = "\n\n".join([
            f"**{p['name']}**\n{p.get('description', '')}\nTechnologies: {p.get('technologies', '')}\nAchievements: {p.get('achievements', 'N/A')}"
            for p in profile_data.get('projects', [])
        ]) or "No projects provided"
        
        skills_text = ", ".join([s['name'] for s in profile_data.get('skills', [])]) or "No skills listed"
        
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            name=profile_data.get('name', 'User'),
            summary=profile_data.get('summary', 'No summary provided'),
            education=education_text,
            experiences=experiences_text,
            projects=projects_text,
            skills=skills_text
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
        
        logger.info(f"Profile summarized: {len(result.get('experience_summaries', []))} experiences, {len(result.get('project_summaries', []))} projects")
        return result
    
    def _summarize_fallback(self, profile_data: Dict) -> Dict:
        """Fallback rules-based summarization."""
        experience_summaries = []
        for exp in profile_data.get('experiences', []):
            bullets = []
            if exp.get('description'):
                bullets.append(exp['description'])
            if exp.get('achievements'):
                achievements = exp['achievements'].split('\n')
                bullets.extend([a.strip() for a in achievements if a.strip()])
            
            experience_summaries.append({
                "title": exp['title'],
                "company": exp['company'],
                "period": f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present' if exp.get('current') else '')}",
                "bullets": bullets[:5] if bullets else ["Contributed to company objectives"],
                "key_skills": [],
                "impact_areas": []
            })
        
        project_summaries = []
        for proj in profile_data.get('projects', []):
            bullets = []
            if proj.get('description'):
                bullets.append(proj['description'])
            if proj.get('achievements'):
                bullets.extend([a.strip() for a in proj['achievements'].split('\n') if a.strip()])
            
            project_summaries.append({
                "name": proj['name'],
                "bullets": bullets[:3] if bullets else ["Developed project"],
                "technologies": proj.get('technologies', '').split(',') if proj.get('technologies') else [],
                "impact_areas": []
            })
        
        skills_by_category = {}
        for skill in profile_data.get('skills', []):
            cat = skill.get('category', 'general')
            if cat not in skills_by_category:
                skills_by_category[cat] = []
            skills_by_category[cat].append(skill['name'])
        
        education_summary = [{
            "degree": e['degree'],
            "institution": e['institution'],
            "highlights": [e.get('achievements', '')] if e.get('achievements') else []
        } for e in profile_data.get('education', [])]
        
        return {
            "experience_summaries": experience_summaries,
            "project_summaries": project_summaries,
            "skill_summary": skills_by_category or {"technical": [], "soft": [], "domain": []},
            "education_summary": education_summary
        }
