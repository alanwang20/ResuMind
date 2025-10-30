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
        """
        Improved fallback parser with proper section segmentation and bullet extraction.
        No longer creates empty placeholder records.
        """
        logger.info("Using fallback resume parser")
        
        import re
        
        lines = [line.rstrip() for line in resume_text.split('\n')]
        
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
        
        # Extract personal info from header
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
                linkedin_match = re.search(r'linkedin\.com/in/[A-Za-z0-9_-]+', line.lower())
                if linkedin_match:
                    result['personal_info']['linkedin'] = f"https://{linkedin_match.group()}"
        
        if lines:
            result['personal_info']['name'] = lines[0].strip()
        
        # Section headers
        section_patterns = {
            'education': r'\b(EDUCATION|Academic Background)\b',
            'experience': r'\b(RELEVANT EXPERIENCE|EXPERIENCE|WORK HISTORY|PROFESSIONAL EXPERIENCE|Employment)\b',
            'skills': r'\b(SKILLS|TECHNICAL SKILLS|COMPETENCIES|Technologies)\b',
            'projects': r'\b(PROJECTS|PORTFOLIO|PERSONAL PROJECTS)\b',
            'leadership': r'\b(LEADERSHIP|ACADEMIC INVOVLEMENT|ACTIVITIES)\b'
        }
        
        # Find section boundaries
        sections = {}
        for i, line in enumerate(lines):
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    sections[section_name] = i
                    break
        
        # Sort sections by line number
        sorted_sections = sorted(sections.items(), key=lambda x: x[1])
        
        # Process each section
        for idx, (section_name, start_line) in enumerate(sorted_sections):
            # Find end of section (start of next section or end of document)
            end_line = sorted_sections[idx + 1][1] if idx + 1 < len(sorted_sections) else len(lines)
            section_lines = lines[start_line + 1:end_line]
            
            if section_name == 'education':
                result['education'] = self._extract_education(section_lines)
            elif section_name == 'experience':
                result['experience'] = self._extract_experience(section_lines)
            elif section_name == 'skills':
                result['skills'] = self._extract_skills(section_lines)
            elif section_name == 'projects':
                result['projects'] = self._extract_projects(section_lines)
        
        logger.info(f"Fallback parsing completed: {len(result['education'])} education, {len(result['experience'])} experience, {len(result['skills'])} skills, {len(result['projects'])} projects")
        return result
    
    def _extract_education(self, lines: list) -> list:
        """Extract education entries from section lines."""
        import re
        education = []
        current = None
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if it's a new institution (usually in all caps or followed by degree info)
            if line_stripped and (line_stripped.isupper() or any(deg in line.lower() for deg in ['university', 'institute', 'college'])):
                if current and (current.get('institution') or current.get('degree')):
                    education.append(current)
                current = {
                    'institution': line_stripped,
                    'degree': '',
                    'field_of_study': '',
                    'start_date': '',
                    'end_date': '',
                    'gpa': '',
                    'achievements': ''
                }
            elif current:
                # Look for degree information
                if any(deg in line.lower() for deg in ['b.b.a', 'b.a.', 'b.s.', 'm.s.', 'm.a.', 'master', 'bachelor', 'phd', 'ph.d']):
                    current['degree'] = line_stripped
                    # Extract field of study (usually in parentheses)
                    field_match = re.search(r'\(([^)]+)\)', line)
                    if field_match:
                        current['field_of_study'] = field_match.group(1)
                # Look for dates (capture full month-year pairs)
                elif re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d{2})', line):
                    # Capture complete date strings like "Aug 2024" or "2024"
                    dates = re.findall(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+20\d{2}|20\d{2})', line)
                    if len(dates) >= 2:
                        current['start_date'] = dates[0]
                        current['end_date'] = dates[1]
                    elif len(dates) == 1:
                        current['end_date'] = dates[0]
                # Look for GPA
                elif 'gpa' in line.lower():
                    gpa_match = re.search(r'(\d\.\d{1,2})', line)
                    if gpa_match:
                        current['gpa'] = gpa_match.group(1)
        
        if current and (current.get('institution') or current.get('degree')):
            education.append(current)
        
        return education
    
    def _extract_experience(self, lines: list) -> list:
        """Extract work experience with ALL bullet points."""
        import re
        experiences = []
        current = None
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                if current:
                    # Empty line might signal end of entry
                    pass
                continue
            
            # Check if it's a company name (usually in all caps)
            if line_stripped.isupper() and len(line_stripped) > 3:
                if current and current.get('company'):
                    experiences.append(current)
                current = {
                    'company': line_stripped,
                    'title': '',
                    'location': '',
                    'start_date': '',
                    'end_date': '',
                    'current': False,
                    'description': '',
                    'achievements': ''
                }
            elif current:
                # Check if it's a job title with dates
                date_match = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+20\d{2}|20\d{2}', line)
                if date_match and not current.get('title'):
                    # This line contains title and dates
                    parts = line_stripped.split(',')
                    if parts:
                        current['title'] = parts[0].strip()
                    # Extract complete date strings like "May 2024"
                    dates = re.findall(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+20\d{2}|20\d{2})', line)
                    if len(dates) >= 2:
                        current['start_date'] = dates[0]
                        current['end_date'] = dates[1]
                    elif len(dates) == 1:
                        if 'present' in line.lower():
                            current['start_date'] = dates[0]
                            current['end_date'] = 'Present'
                            current['current'] = True
                        else:
                            current['end_date'] = dates[0]
                # Check if it's a bullet point
                elif line_stripped.startswith('●') or line_stripped.startswith('•') or line_stripped.startswith('-'):
                    bullet = line_stripped.lstrip('●•- ').strip()
                    if current.get('achievements'):
                        current['achievements'] += '\n' + bullet
                    else:
                        current['achievements'] = bullet
        
        if current and current.get('company'):
            experiences.append(current)
        
        return experiences
    
    def _extract_skills(self, lines: list) -> list:
        """Extract skills from section."""
        import re
        skills = []
        current_category = 'Technical Skills'
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if it's a category (usually ends with :)
            if ':' in line_stripped and len(line_stripped) < 50:
                parts = line_stripped.split(':', 1)
                current_category = parts[0].strip()
                # Extract skills from same line
                if len(parts) > 1:
                    skills_text = parts[1]
                    skill_names = [s.strip() for s in re.split(r'[,;•|]', skills_text) if s.strip()]
                    for skill_name in skill_names:
                        if skill_name and len(skill_name) > 1:
                            skills.append({
                                'name': skill_name,
                                'category': current_category,
                                'proficiency': ''
                            })
            else:
                # Extract all skills from line
                skill_names = [s.strip() for s in re.split(r'[,;•|]', line_stripped) if s.strip()]
                for skill_name in skill_names:
                    if skill_name and len(skill_name) > 1 and len(skill_name) < 100:
                        skills.append({
                            'name': skill_name,
                            'category': current_category,
                            'proficiency': ''
                        })
        
        return skills
    
    def _extract_projects(self, lines: list) -> list:
        """Extract projects from section."""
        import re
        projects = []
        current = None
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if it's a project name (usually followed by date or description)
            if not line_stripped.startswith('●') and not line_stripped.startswith('•') and not line_stripped.startswith('-'):
                if current and current.get('name'):
                    projects.append(current)
                # Extract date if present
                date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d{2})', line_stripped)
                if date_match:
                    name_parts = line_stripped.split(date_match.group(0))
                    current = {
                        'name': name_parts[0].strip(),
                        'description': '',
                        'technologies': '',
                        'url': '',
                        'achievements': ''
                    }
                else:
                    current = {
                        'name': line_stripped,
                        'description': '',
                        'technologies': '',
                        'url': '',
                        'achievements': ''
                    }
            elif current:
                # It's a bullet point
                bullet = line_stripped.lstrip('●•- ').strip()
                if current.get('achievements'):
                    current['achievements'] += '\n' + bullet
                else:
                    current['achievements'] = bullet
        
        if current and current.get('name'):
            projects.append(current)
        
        return projects
