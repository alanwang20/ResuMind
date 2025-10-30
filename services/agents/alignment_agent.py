import logging
import json
from typing import Dict
from openai import OpenAI
import html

logger = logging.getLogger(__name__)


class AlignmentAgent:
    """
    Agent 3: Aligns user experiences with role requirements.
    Takes company insights and experience summaries to create a tailored resume.
    """
    
    SYSTEM_PROMPT = """You are an expert resume strategist who excels at matching candidate experiences to specific job requirements.

Your task is to:
1. Rank experiences by relevance to the target role
2. Tailor bullet points to match company preferences and keywords
3. Highlight the most impactful achievements for this specific role
4. Follow company-specific formatting preferences
5. Ensure key requirements are addressed

Create a polished, ATS-optimized resume that maximizes the candidate's chances."""

    USER_PROMPT_TEMPLATE = """Create a tailored resume for the following candidate and role:

**Target Role:**
Company: {company_name}
Position: {role_title}

**Company Insights:**
{company_insights}

**Candidate Profile:**
{profile_summary}

**Task:**
1. Select and rank the most relevant experiences for this role
2. Tailor bullet points to match the company's preferred style and keywords
3. Highlight skills and achievements that align with key requirements
4. Format according to company preferences
5. Ensure all important keywords from the job posting are naturally incorporated

Return a JSON object with this structure:
{{
    "resume_html": "<div class='resume-container'>...professionally formatted HTML resume...</div>",
    "resume_md": "# Markdown formatted resume",
    "relevance_scores": {{
        "experience_id": "score and reasoning"
    }},
    "keyword_coverage": {{
        "covered": ["keyword1", "keyword2"],
        "emphasized": ["keyword3", "keyword4"]
    }},
    "tailoring_notes": [
        "Note about how experiences were tailored"
    ]
}}

For the HTML resume, use semantic tags and these classes:
- resume-container, resume-header, resume-section, resume-title, resume-job, resume-bullet

Return ONLY the JSON object."""

    def __init__(self, use_openai: bool = True):
        self.use_openai = use_openai
        if use_openai:
            try:
                self.client = OpenAI()
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.use_openai = False
    
    def align(self, company_insights: Dict, experience_summaries: Dict, role_data: Dict, profile_data: Dict) -> Dict:
        """
        Create aligned resume matching experiences to role.
        
        Args:
            company_insights: Output from Company Insight Agent
            experience_summaries: Output from Experience Summarizer Agent
            role_data: Role submission data
            profile_data: User profile data
        
        Returns:
            Dict with resume_html, resume_md, relevance_scores, keyword_coverage
        """
        logger.info(f"Alignment Agent creating tailored resume for: {role_data['role_title']}")
        
        if self.use_openai:
            try:
                return self._align_with_openai(company_insights, experience_summaries, role_data, profile_data)
            except Exception as e:
                logger.error(f"OpenAI alignment failed: {e}, falling back to rules-based")
                return self._align_fallback(company_insights, experience_summaries, role_data, profile_data)
        else:
            return self._align_fallback(company_insights, experience_summaries, role_data, profile_data)
    
    def _align_with_openai(self, company_insights: Dict, experience_summaries: Dict, role_data: Dict, profile_data: Dict) -> Dict:
        """Use OpenAI to create aligned resume."""
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            company_name=role_data['company_name'],
            role_title=role_data['role_title'],
            company_insights=json.dumps(company_insights, indent=2),
            profile_summary=json.dumps(experience_summaries, indent=2)
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
        
        import bleach
        ALLOWED_TAGS = ['h1', 'h2', 'h3', 'h4', 'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'div', 'span', 'a']
        ALLOWED_ATTRIBUTES = {'*': ['class', 'id'], 'a': ['href', 'title']}
        
        if 'resume_html' in result:
            result['resume_html'] = bleach.clean(
                result['resume_html'],
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                strip=True
            )
        
        logger.info(f"Aligned resume created with {len(result.get('keyword_coverage', {}).get('covered', []))} keywords covered")
        return result
    
    def _align_fallback(self, company_insights: Dict, experience_summaries: Dict, role_data: Dict, profile_data: Dict) -> Dict:
        """Fallback rules-based alignment."""
        important_keywords = set(company_insights.get('important_keywords', []))
        
        name = html.escape(profile_data.get('name', 'Your Name'))
        email = html.escape(profile_data.get('email', 'your.email@example.com'))
        phone = html.escape(profile_data.get('phone', '(555) 123-4567'))
        location = html.escape(profile_data.get('location', ''))
        
        experience_html = ""
        for exp in experience_summaries.get('experience_summaries', [])[:3]:
            title = html.escape(exp['title'])
            company = html.escape(exp['company'])
            period = html.escape(exp['period'])
            
            bullets_html = ""
            for bullet in exp['bullets'][:4]:
                escaped_bullet = html.escape(bullet)
                bullets_html += f"        <li class='resume-bullet'>{escaped_bullet}</li>\n"
            
            experience_html += f"""    <div class="resume-job">
        <h3>{title} - {company}</h3>
        <p class="period">{period}</p>
        <ul>
{bullets_html}        </ul>
    </div>
    """
        
        skills_list = []
        for category, skills in experience_summaries.get('skill_summary', {}).items():
            skills_list.extend(skills[:5])
        skills_text = ' • '.join([html.escape(s) for s in skills_list[:15]])
        
        education_html = ""
        for edu in experience_summaries.get('education_summary', []):
            degree = html.escape(edu['degree'])
            institution = html.escape(edu['institution'])
            education_html += f"        <p><strong>{degree}</strong> - {institution}</p>\n"
        
        resume_html = f"""<div class="resume-container">
    <div class="resume-header">
        <h1>{name}</h1>
        <p>{email} | {phone}{' | ' + location if location else ''}</p>
    </div>
    
    <div class="resume-section">
        <h2 class="resume-title">Experience</h2>
{experience_html}    </div>
    
    <div class="resume-section">
        <h2 class="resume-title">Skills</h2>
        <p>{skills_text}</p>
    </div>
    
    <div class="resume-section">
        <h2 class="resume-title">Education</h2>
{education_html}    </div>
</div>"""
        
        resume_md = f"""# {profile_data.get('name', 'Your Name')}
{profile_data.get('email', '')} | {profile_data.get('phone', '')}

## Experience
""" + "\n\n".join([f"### {exp['title']} - {exp['company']}\n{exp['period']}\n" + "\n".join([f"- {b}" for b in exp['bullets'][:4]]) 
                     for exp in experience_summaries.get('experience_summaries', [])[:3]])
        
        resume_md += f"\n\n## Skills\n{', '.join(skills_list[:15])}"
        
        if experience_summaries.get('education_summary'):
            resume_md += "\n\n## Education\n" + "\n".join([f"**{e['degree']}** - {e['institution']}" 
                                                           for e in experience_summaries.get('education_summary', [])])
        
        covered_keywords = [kw for kw in important_keywords if kw in resume_html.lower()]
        
        return {
            "resume_html": resume_html,
            "resume_md": resume_md,
            "relevance_scores": {},
            "keyword_coverage": {
                "covered": covered_keywords[:20],
                "emphasized": covered_keywords[:10]
            },
            "tailoring_notes": ["Resume tailored using fallback mode"]
        }
