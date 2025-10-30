import os
import uuid
import logging
from flask import Flask, render_template, request, redirect, url_for, session, Response
import json
import bleach

from models import db
from models.user_profile import UserProfile, Education, Experience, Skill, Project, RoleSubmission
from services.orchestration import ResumeOrchestrator

ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'strong', 'em', 'u', 'b', 'i',
    'ul', 'ol', 'li',
    'div', 'span',
    'a'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id'],
    'a': ['href', 'title'],
    'div': ['class', 'id'],
    'span': ['class', 'id'],
}


def sanitize_html(html_content: str) -> str:
    """Sanitize HTML content to prevent XSS attacks."""
    if not html_content:
        return ""
    return bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resumind.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024

db.init_app(app)

openai_available = os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_BASE_URL')
orchestrator = ResumeOrchestrator(use_openai=bool(openai_available))


with app.app_context():
    db.create_all()
    logger.info("Database tables created")


@app.route('/')
def index():
    """Page 1: Profile input form."""
    return render_template('profile_form.html')


@app.route('/profile', methods=['POST'])
def save_profile():
    """Save user profile and redirect to role input page."""
    try:
        session_id = str(uuid.uuid4())
        
        profile = UserProfile(
            session_id=session_id,
            name=request.form.get('name', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            location=request.form.get('location', '').strip(),
            linkedin=request.form.get('linkedin', '').strip(),
            website=request.form.get('website', '').strip(),
            summary=request.form.get('summary', '').strip()
        )
        
        db.session.add(profile)
        db.session.flush()
        
        education_data = request.form.getlist('education_degree')
        for i, degree in enumerate(education_data):
            if degree.strip():
                education = Education(
                    profile_id=profile.id,
                    degree=degree.strip(),
                    field_of_study=request.form.getlist('education_field')[i] if i < len(request.form.getlist('education_field')) else '',
                    institution=request.form.getlist('education_institution')[i] if i < len(request.form.getlist('education_institution')) else '',
                    start_date=request.form.getlist('education_start')[i] if i < len(request.form.getlist('education_start')) else '',
                    end_date=request.form.getlist('education_end')[i] if i < len(request.form.getlist('education_end')) else '',
                    gpa=request.form.getlist('education_gpa')[i] if i < len(request.form.getlist('education_gpa')) else '',
                    achievements=request.form.getlist('education_achievements')[i] if i < len(request.form.getlist('education_achievements')) else ''
                )
                db.session.add(education)
        
        experience_titles = request.form.getlist('experience_title')
        for i, title in enumerate(experience_titles):
            if title.strip():
                experience = Experience(
                    profile_id=profile.id,
                    title=title.strip(),
                    company=request.form.getlist('experience_company')[i] if i < len(request.form.getlist('experience_company')) else '',
                    location=request.form.getlist('experience_location')[i] if i < len(request.form.getlist('experience_location')) else '',
                    start_date=request.form.getlist('experience_start')[i] if i < len(request.form.getlist('experience_start')) else '',
                    end_date=request.form.getlist('experience_end')[i] if i < len(request.form.getlist('experience_end')) else '',
                    current='experience_current_' + str(i) in request.form,
                    description=request.form.getlist('experience_description')[i] if i < len(request.form.getlist('experience_description')) else '',
                    achievements=request.form.getlist('experience_achievements')[i] if i < len(request.form.getlist('experience_achievements')) else ''
                )
                db.session.add(experience)
        
        skill_names = request.form.getlist('skill_name')
        for i, name in enumerate(skill_names):
            if name.strip():
                skill = Skill(
                    profile_id=profile.id,
                    name=name.strip(),
                    category=request.form.getlist('skill_category')[i] if i < len(request.form.getlist('skill_category')) else '',
                    proficiency=request.form.getlist('skill_proficiency')[i] if i < len(request.form.getlist('skill_proficiency')) else ''
                )
                db.session.add(skill)
        
        project_names = request.form.getlist('project_name')
        for i, name in enumerate(project_names):
            if name.strip():
                project = Project(
                    profile_id=profile.id,
                    name=name.strip(),
                    description=request.form.getlist('project_description')[i] if i < len(request.form.getlist('project_description')) else '',
                    technologies=request.form.getlist('project_technologies')[i] if i < len(request.form.getlist('project_technologies')) else '',
                    url=request.form.getlist('project_url')[i] if i < len(request.form.getlist('project_url')) else '',
                    achievements=request.form.getlist('project_achievements')[i] if i < len(request.form.getlist('project_achievements')) else ''
                )
                db.session.add(project)
        
        db.session.commit()
        logger.info(f"Profile saved with session_id: {session_id}")
        
        return redirect(url_for('role_input', session_id=session_id))
    
    except Exception as e:
        logger.error(f"Error saving profile: {e}", exc_info=True)
        db.session.rollback()
        return render_template('profile_form.html', error=str(e)), 500


@app.route('/role/<session_id>')
def role_input(session_id):
    """Page 2: Role and company input form."""
    profile = UserProfile.query.filter_by(session_id=session_id).first()
    if not profile:
        return redirect(url_for('index'))
    
    return render_template('role_form.html', session_id=session_id, profile=profile)


@app.route('/generate_resume', methods=['POST'])
def generate_resume():
    """Generate tailored resume using multi-agent system."""
    try:
        session_id = request.form.get('session_id')
        profile = UserProfile.query.filter_by(session_id=session_id).first()
        
        if not profile:
            return render_template('error.html', error="Profile not found"), 404
        
        role_submission = RoleSubmission(
            profile_id=profile.id,
            company_name=request.form.get('company_name', '').strip(),
            role_title=request.form.get('role_title', '').strip(),
            job_description=request.form.get('job_description', '').strip(),
            company_info=request.form.get('company_info', '').strip()
        )
        
        db.session.add(role_submission)
        db.session.flush()
        
        profile_data = profile.to_dict()
        role_data = {
            'company_name': role_submission.company_name,
            'role_title': role_submission.role_title,
            'job_description': role_submission.job_description,
            'company_info': role_submission.company_info or ''
        }
        
        logger.info(f"Generating resume for {role_submission.role_title} at {role_submission.company_name}")
        result = orchestrator.generate_tailored_resume(profile_data, role_data)
        
        if result.get('aligned_resume', {}).get('resume_html'):
            result['aligned_resume']['resume_html'] = sanitize_html(result['aligned_resume']['resume_html'])
            logger.info("Resume HTML sanitized before storage and rendering")
        
        role_submission.company_insights = json.dumps(result.get('company_insights', {}))
        role_submission.experience_summaries = json.dumps(result.get('experience_summaries', {}))
        role_submission.aligned_resume = json.dumps(result.get('aligned_resume', {}))
        
        db.session.commit()
        
        return render_template('resume_result.html',
                             session_id=session_id,
                             submission_id=role_submission.id,
                             profile=profile,
                             role=role_submission,
                             result=result)
    
    except Exception as e:
        logger.error(f"Error generating resume: {e}", exc_info=True)
        db.session.rollback()
        return render_template('error.html', error=str(e)), 500


@app.route('/download/resume/<int:submission_id>')
def download_resume(submission_id):
    """Download resume as Markdown."""
    submission = RoleSubmission.query.get_or_404(submission_id)
    
    try:
        aligned_resume = json.loads(submission.aligned_resume) if submission.aligned_resume else {}
        resume_md = aligned_resume.get('resume_md', '# Resume\nNo content available')
        
        return Response(
            resume_md,
            mimetype='text/markdown',
            headers={'Content-Disposition': f'attachment; filename=resume_{submission.company_name}_{submission.role_title}.md'}
        )
    except Exception as e:
        logger.error(f"Error downloading resume: {e}")
        return "Error downloading resume", 500


@app.route('/agent_status')
def agent_status():
    """Debug endpoint to check agent statuses."""
    return orchestrator.get_agent_statuses()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
