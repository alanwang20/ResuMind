import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ResumeParserAgent:
    def __init__(self, openai_client=None):
        self.client = openai_client
        self.use_openai = openai_client is not None
        logger.info(f"ResumeParserAgent initialized (OpenAI: {self.use_openai})")
    
    def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        if self.use_openai:
            return self._parse_with_openai(resume_text)
        else:
            return self._parse_with_fallback(resume_text)
    
    def _parse_with_openai(self, resume_text: str) -> Dict[str, Any]:
        try:
            prompt = f"""You are a resume parsing expert. Extract structured information from the following resume text.

Resume Text:
{resume_text}

Extract and return a JSON object with the following structure:
{{
  "personal_info": {{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "phone number",
    "location": "City, State",
    "linkedin": "LinkedIn URL",
    "website": "Portfolio/Website URL",
    "summary": "Professional summary or objective"
  }},
  "education": [
    {{
      "degree": "Degree type (e.g., Bachelor of Science)",
      "field_of_study": "Major/Field",
      "institution": "University name",
      "location": "City, State",
      "start_date": "Start date",
      "end_date": "End date or 'Present'",
      "gpa": "GPA if mentioned",
      "achievements": "Honors, awards, relevant coursework"
    }}
  ],
  "experience": [
    {{
      "title": "Job title",
      "company": "Company name",
      "location": "City, State",
      "start_date": "Start date",
      "end_date": "End date or 'Present'",
      "current": true/false,
      "description": "Brief role description",
      "achievements": "Key accomplishments and responsibilities"
    }}
  ],
  "skills": [
    {{
      "name": "Skill name",
      "category": "Category (e.g., Programming Languages, Tools, Soft Skills)",
      "proficiency": "Proficiency level if mentioned"
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "description": "Project description",
      "technologies": "Technologies used",
      "url": "Project URL if available",
      "achievements": "Key outcomes and impact"
    }}
  ]
}}

Instructions:
- Extract all available information accurately
- If a field is not found, use an empty string ""
- For dates, use the format provided in the resume
- For 'current' field, set to true if the person is still in that role
- Group skills by logical categories (Programming Languages, Frameworks, Tools, etc.)
- Be thorough in extracting achievements and accomplishments
- Return ONLY valid JSON, no additional text"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise resume parsing assistant that extracts structured data from resumes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info("Resume parsed successfully with OpenAI")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI parsing failed: {e}", exc_info=True)
            return self._parse_with_fallback(resume_text)
    
    def _parse_with_fallback(self, resume_text: str) -> Dict[str, Any]:
        logger.info("Using fallback resume parser")
        
        lines = resume_text.split('\n')
        
        result = {
            "personal_info": {
                "name": "",
                "email": "",
                "phone": "",
                "location": "",
                "linkedin": "",
                "website": "",
                "summary": ""
            },
            "education": [],
            "experience": [],
            "skills": [],
            "projects": []
        }
        
        import re
        
        for line in lines[:10]:
            if '@' in line and not result['personal_info']['email']:
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)
                if email_match:
                    result['personal_info']['email'] = email_match.group()
            
            if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', line) and not result['personal_info']['phone']:
                phone_match = re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', line)
                if phone_match:
                    result['personal_info']['phone'] = phone_match.group()
            
            if 'linkedin.com' in line.lower() and not result['personal_info']['linkedin']:
                result['personal_info']['linkedin'] = line.strip()
        
        if lines and not result['personal_info']['name']:
            result['personal_info']['name'] = lines[0].strip()
        
        education_keywords = ['education', 'academic', 'university', 'college', 'bachelor', 'master', 'phd', 'degree']
        experience_keywords = ['experience', 'employment', 'work history', 'professional']
        skills_keywords = ['skills', 'technical skills', 'competencies', 'technologies']
        projects_keywords = ['projects', 'portfolio']
        
        current_section = None
        section_content = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if any(keyword in line_lower for keyword in education_keywords) and len(line_lower) < 50:
                current_section = 'education'
                continue
            elif any(keyword in line_lower for keyword in experience_keywords) and len(line_lower) < 50:
                current_section = 'experience'
                continue
            elif any(keyword in line_lower for keyword in skills_keywords) and len(line_lower) < 50:
                current_section = 'skills'
                continue
            elif any(keyword in line_lower for keyword in projects_keywords) and len(line_lower) < 50:
                current_section = 'projects'
                continue
            
            if current_section and line.strip():
                section_content.append(line.strip())
        
        if section_content:
            result['personal_info']['summary'] = "Please review and edit the extracted information."
        
        logger.info("Fallback parsing completed")
        return result
