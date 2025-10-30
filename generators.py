import os
import re
import time
from typing import Dict
import logging
import html
import bleach

from prompts import (
    RESUME_SYSTEM, RESUME_USER_TEMPLATE,
    QUESTIONS_SYSTEM, QUESTIONS_USER_TEMPLATE
)
from utils import simple_ats_report, top_ngrams

logger = logging.getLogger(__name__)

ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'strong', 'em', 'u', 'b', 'i',
    'ul', 'ol', 'li',
    'div', 'span',
    'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id'],
    'a': ['href', 'title'],
    'div': ['class', 'id'],
    'span': ['class', 'id'],
}


def sanitize_html(html_content: str) -> str:
    """Sanitize HTML content to prevent XSS attacks."""
    return bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )


def extract_tagged_content(text: str, tag: str) -> str:
    """Extract content between XML-like tags."""
    pattern = f'<{tag}>(.*?)</{tag}>'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def generate_with_openai(payload: Dict) -> Dict:
    """
    Generate resume and interview questions using OpenAI API.
    
    Args:
        payload: dict with 'job_description' and 'user_experience'
    
    Returns:
        dict with 'resume_html', 'resume_md', 'questions_md', 'ats_report'
    """
    try:
        from openai import OpenAI
        
        client = OpenAI()
        
        job_desc = payload['job_description']
        user_exp = payload['user_experience']
        
        start_time = time.time()
        
        resume_user_prompt = RESUME_USER_TEMPLATE.format(
            job_description=job_desc,
            user_experience=user_exp
        )
        
        logger.info(f"Calling OpenAI for resume generation...")
        logger.info(f"Resume prompt length: {len(resume_user_prompt)} chars")
        
        resume_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": RESUME_SYSTEM},
                {"role": "user", "content": resume_user_prompt}
            ],
            temperature=0.4
        )
        
        resume_content = resume_response.choices[0].message.content or ""
        resume_time = time.time() - start_time
        logger.info(f"Resume generated in {resume_time:.2f}s, response length: {len(resume_content)} chars")
        
        resume_html = extract_tagged_content(resume_content, 'RESUME_HTML')
        resume_md = extract_tagged_content(resume_content, 'RESUME_MD')
        
        if not resume_html or not resume_md:
            logger.warning("Could not extract HTML or MD from resume response, using raw content")
            resume_html = f"<div class='resume-content'>{html.escape(resume_content)}</div>"
            resume_md = resume_content
        else:
            resume_html = sanitize_html(resume_html)
        
        start_time = time.time()
        
        questions_user_prompt = QUESTIONS_USER_TEMPLATE.format(
            job_description=job_desc,
            user_experience=user_exp
        )
        
        logger.info(f"Calling OpenAI for interview questions...")
        logger.info(f"Questions prompt length: {len(questions_user_prompt)} chars")
        
        questions_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": QUESTIONS_SYSTEM},
                {"role": "user", "content": questions_user_prompt}
            ],
            temperature=0.5
        )
        
        questions_content = questions_response.choices[0].message.content or ""
        questions_time = time.time() - start_time
        logger.info(f"Questions generated in {questions_time:.2f}s, response length: {len(questions_content)} chars")
        
        questions_md = extract_tagged_content(questions_content, 'QUESTIONS_MD')
        
        if not questions_md:
            logger.warning("Could not extract questions MD, using raw content")
            questions_md = questions_content
        
        ats_report = simple_ats_report(job_desc, user_exp)
        
        return {
            'resume_html': resume_html,
            'resume_md': resume_md,
            'questions_md': questions_md,
            'ats_report': ats_report
        }
        
    except Exception as e:
        logger.error(f"OpenAI generation failed: {e}")
        raise


def generate_fallback(payload: Dict) -> Dict:
    """
    Fallback generator using rules-based templates.
    
    Args:
        payload: dict with 'job_description' and 'user_experience'
    
    Returns:
        dict with 'resume_html', 'resume_md', 'questions_md', 'ats_report'
    """
    logger.info("Using fallback generator (rules-based)")
    
    job_desc = payload['job_description']
    user_exp = payload['user_experience']
    
    keywords = top_ngrams(job_desc, top_k=15)
    top_skills = [kw for kw, _ in keywords[:10]]
    
    experience_lines = [line.strip() for line in user_exp.split('\n') if line.strip()]
    experience_bullets = experience_lines[:8]
    
    action_verbs = ['Developed', 'Led', 'Implemented', 'Designed', 'Managed', 'Created', 'Optimized', 'Coordinated']
    
    formatted_bullets = []
    for i, bullet in enumerate(experience_bullets):
        verb = action_verbs[i % len(action_verbs)]
        if not bullet[0].isupper():
            bullet = f"{verb} {bullet}"
        formatted_bullets.append(html.escape(bullet))
    
    escaped_skills = [html.escape(skill) for skill in top_skills]
    
    resume_html = f"""<div class="resume-container">
    <div class="resume-header">
        <h1>Your Name</h1>
        <p>Email: your.email@example.com | Phone: (555) 123-4567</p>
    </div>
    
    <div class="resume-section">
        <h2 class="resume-title">Professional Summary</h2>
        <p>Results-driven professional with expertise in {', '.join(escaped_skills[:3])}. Proven track record in delivering high-impact projects and driving organizational success.</p>
    </div>
    
    <div class="resume-section">
        <h2 class="resume-title">Experience</h2>
        <div class="resume-job">
            <h3>Professional Experience</h3>
            <ul>
                {''.join([f'<li class="resume-bullet">{bullet}</li>' for bullet in formatted_bullets])}
            </ul>
        </div>
    </div>
    
    <div class="resume-section">
        <h2 class="resume-title">Skills</h2>
        <p>{' • '.join(escaped_skills)}</p>
    </div>
    
    <div class="resume-section">
        <h2 class="resume-title">Education</h2>
        <p><strong>Bachelor's Degree</strong> - Your University<br>Relevant coursework and achievements</p>
    </div>
</div>"""
    
    resume_md = f"""# Your Name
Email: your.email@example.com | Phone: (555) 123-4567

## Professional Summary
Results-driven professional with expertise in {', '.join(top_skills[:3])}. Proven track record in delivering high-impact projects and driving organizational success.

## Experience

### Professional Experience
{chr(10).join([f'- {bullet}' for bullet in formatted_bullets])}

## Skills
{' • '.join(top_skills)}

## Education
**Bachelor's Degree** - Your University  
Relevant coursework and achievements
"""
    
    questions_md = f"""# Interview Preparation Questions

## Behavioral Questions

**Behavioral Q1:** Tell me about a time when you faced a significant challenge in a project. How did you overcome it?
*Tip:* Use the STAR method (Situation, Task, Action, Result) to structure your answer.

**Behavioral Q2:** Describe a situation where you had to work with a difficult team member.
*Tip:* Focus on your problem-solving approach and positive outcome.

**Behavioral Q3:** Give an example of when you had to meet a tight deadline.
*Tip:* Highlight your time management and prioritization skills.

**Behavioral Q4:** Tell me about a time you failed. What did you learn?
*Tip:* Show self-awareness and growth mindset.

## Technical Questions

**Technical Q1:** What experience do you have with {top_skills[0] if top_skills else 'the key technologies'} mentioned in the job description?
*Tip:* Provide specific examples and measurable outcomes.

**Technical Q2:** How would you approach {top_skills[1] if len(top_skills) > 1 else 'solving a complex problem'} in this role?
*Tip:* Walk through your thought process step-by-step.

**Technical Q3:** What are the best practices you follow when {top_skills[2] if len(top_skills) > 2 else 'working on projects'}?
*Tip:* Show you understand industry standards and quality.

**Technical Q4:** Can you explain a complex technical concept to a non-technical stakeholder?
*Tip:* Demonstrate communication skills with a clear example.

## Team Fit Questions

**Team Fit Q1:** What type of work environment helps you thrive?
*Tip:* Be honest but align with the company culture you researched.

**Team Fit Q2:** How do you handle feedback and criticism?
*Tip:* Show you're open to growth and continuous improvement.
"""
    
    ats_report = simple_ats_report(job_desc, user_exp)
    
    return {
        'resume_html': resume_html,
        'resume_md': resume_md,
        'questions_md': questions_md,
        'ats_report': ats_report
    }
