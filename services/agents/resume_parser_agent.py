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
        
        lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
        
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
        
        for line in lines[:15]:
            if '@' in line and not result['personal_info']['email']:
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)
                if email_match:
                    result['personal_info']['email'] = email_match.group()
            
            if not result['personal_info']['phone']:
                phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', line)
                if phone_match:
                    result['personal_info']['phone'] = phone_match.group()
            
            if 'linkedin.com' in line.lower() and not result['personal_info']['linkedin']:
                result['personal_info']['linkedin'] = line.strip()
            
            if ('http' in line.lower() or 'www.' in line.lower()) and not result['personal_info']['website']:
                if 'linkedin' not in line.lower():
                    result['personal_info']['website'] = line.strip()
        
        if lines and not result['personal_info']['name']:
            potential_name = lines[0]
            if len(potential_name) < 50 and not '@' in potential_name:
                result['personal_info']['name'] = potential_name
        
        education_keywords = ['education', 'academic background', 'university', 'college']
        experience_keywords = ['experience', 'employment', 'work history', 'professional experience']
        skills_keywords = ['skills', 'technical skills', 'competencies', 'technologies', 'proficiencies']
        projects_keywords = ['projects', 'portfolio', 'personal projects']
        
        degree_keywords = ['bachelor', 'master', 'phd', 'b.s.', 'm.s.', 'b.a.', 'm.a.', 'associate']
        
        current_section = None
        current_item = {}
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in education_keywords) and len(line) < 50:
                current_section = 'education'
                current_item = {}
                continue
            elif any(keyword in line_lower for keyword in experience_keywords) and len(line) < 50:
                current_section = 'experience'
                current_item = {}
                continue
            elif any(keyword in line_lower for keyword in skills_keywords) and len(line) < 50:
                current_section = 'skills'
                current_item = {}
                continue
            elif any(keyword in line_lower for keyword in projects_keywords) and len(line) < 50:
                current_section = 'projects'
                current_item = {}
                continue
            
            if current_section == 'education':
                if any(deg in line_lower for deg in degree_keywords):
                    if current_item and current_item.get('degree'):
                        result['education'].append(current_item)
                    current_item = {
                        'degree': line,
                        'field_of_study': '',
                        'institution': lines[i+1] if i+1 < len(lines) else '',
                        'start_date': '',
                        'end_date': '',
                        'gpa': '',
                        'achievements': ''
                    }
                    date_match = re.search(r'(19|20)\d{2}', line)
                    if date_match and i+1 < len(lines):
                        current_item['institution'] = lines[i+1]
            
            elif current_section == 'experience':
                if line and len(line) < 100 and i+1 < len(lines):
                    next_line = lines[i+1] if i+1 < len(lines) else ''
                    if re.search(r'(19|20)\d{2}', next_line) or 'present' in next_line.lower():
                        if current_item and current_item.get('title'):
                            result['experience'].append(current_item)
                        current_item = {
                            'title': line,
                            'company': '',
                            'location': '',
                            'start_date': '',
                            'end_date': '',
                            'current': False,
                            'description': '',
                            'achievements': ''
                        }
            
            elif current_section == 'skills':
                skills_in_line = [s.strip() for s in re.split(r'[,;•|]', line) if s.strip() and len(s.strip()) > 2]
                for skill in skills_in_line:
                    if skill and len(skill) < 50:
                        result['skills'].append({
                            'name': skill,
                            'category': 'Technical Skills',
                            'proficiency': ''
                        })
            
            elif current_section == 'projects':
                if line and len(line) < 100 and not line.startswith('-'):
                    if current_item and current_item.get('name'):
                        result['projects'].append(current_item)
                    current_item = {
                        'name': line,
                        'description': '',
                        'technologies': '',
                        'url': '',
                        'achievements': ''
                    }
        
        if current_section == 'education' and current_item and current_item.get('degree'):
            result['education'].append(current_item)
        elif current_section == 'experience' and current_item and current_item.get('title'):
            result['experience'].append(current_item)
        elif current_section == 'projects' and current_item and current_item.get('name'):
            result['projects'].append(current_item)
        
        if not result['education']:
            result['education'].append({
                'degree': '',
                'field_of_study': '',
                'institution': '',
                'start_date': '',
                'end_date': '',
                'gpa': '',
                'achievements': ''
            })
        
        if not result['experience']:
            result['experience'].append({
                'title': '',
                'company': '',
                'location': '',
                'start_date': '',
                'end_date': '',
                'current': False,
                'description': '',
                'achievements': ''
            })
        
        result['personal_info']['summary'] = "Extracted from uploaded resume. Please review and edit."
        
        logger.info(f"Fallback parsing completed: {len(result['education'])} education, {len(result['experience'])} experience, {len(result['skills'])} skills, {len(result['projects'])} projects")
        return result
