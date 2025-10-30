import os
import uuid
import logging
from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify
import json
import bleach
from werkzeug.utils import secure_filename

from models import db
from models.user_profile import UserProfile, Education, Experience, Skill, Project, RoleSubmission
from services.orchestration import ResumeOrchestrator
from services.agents.resume_parser_agent import ResumeParserAgent

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

if openai_available:
    from openai import OpenAI
    openai_client = OpenAI()
    resume_parser = ResumeParserAgent(openai_client=openai_client)
else:
    resume_parser = ResumeParserAgent(openai_client=None)


with app.app_context():
    db.create_all()
    logger.info("Database tables created")


def extract_text_from_file(file):
    """Extract text content from uploaded file (PDF, DOCX, or TXT)."""
    import io
    
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    try:
        if file_ext == 'txt':
            return file.read().decode('utf-8', errors='ignore')
        
        elif file_ext == 'pdf':
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            text = []
            for page in pdf_reader.pages:
                text.append(page.extract_text())
            return '\n'.join(text)
        
        elif file_ext == 'docx':
            from docx import Document
            doc = Document(io.BytesIO(file.read()))
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return '\n'.join(text)
        
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {e}", exc_info=True)
        raise


@app.route('/parse_resume', methods=['POST'])
def parse_resume():
    """Parse uploaded resume and extract structured information."""
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['resume']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        logger.info(f"Parsing resume file: {file.filename}")
        
        resume_text = extract_text_from_file(file)
        
        if not resume_text or len(resume_text.strip()) < 50:
            return jsonify({'error': 'Resume file appears to be empty or too short'}), 400
        
        logger.info(f"Extracted {len(resume_text)} characters from resume")
        
        parsed_data = resume_parser.parse_resume(resume_text)
        
        logger.info("Resume parsed successfully")
        return jsonify(parsed_data)
    
    except ValueError as e:
        logger.error(f"Value error parsing resume: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error parsing resume: {e}", exc_info=True)
        return jsonify({'error': 'Failed to parse resume. Please try again or fill out the form manually.'}), 500


@app.route('/')
def index():
    """Landing page: Upload resume."""
    return render_template('index.html')


@app.route('/upload_and_create_profile', methods=['POST'])
def upload_and_create_profile():
    """Upload resume, parse it, and create profile automatically."""
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['resume']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        logger.info(f"Processing resume upload: {file.filename}")
        
        # Extract text from resume
        resume_text = extract_text_from_file(file)
        
        if not resume_text or len(resume_text.strip()) < 50:
            return jsonify({'error': 'Resume file appears to be empty or too short'}), 400
        
        logger.info(f"Extracted {len(resume_text)} characters from resume")
        
        # Parse resume with AI
        parsed_data = resume_parser.parse_resume(resume_text)
        logger.info("Resume parsed successfully")
        
        # Create user profile automatically from parsed data
        session_id = str(uuid.uuid4())
        
        # Extract personal info
        personal_info = parsed_data.get('personal_info', {})
        
        # Prepare profile data for database
        profile_data = {
            'session_id': session_id,
            'name': sanitize_html(personal_info.get('name', 'User')),
            'email': sanitize_html(personal_info.get('email', '')),
            'phone': sanitize_html(personal_info.get('phone', '')),
            'location': sanitize_html(personal_info.get('location', '')),
            'linkedin': sanitize_html(personal_info.get('linkedin', '')),
            'summary': sanitize_html(personal_info.get('summary', ''))
        }
        
        # Create UserProfile
        user_profile = UserProfile(**profile_data)
        db.session.add(user_profile)
        db.session.flush()  # Get the ID
        
        # Add education entries
        for edu in parsed_data.get('education', []):
            education = Education(
                user_profile_id=user_profile.id,
                degree=sanitize_html(edu.get('degree', '')),
                field_of_study=sanitize_html(edu.get('field_of_study', '')),
                institution=sanitize_html(edu.get('institution', '')),
                start_date=sanitize_html(edu.get('start_date', '')),
                end_date=sanitize_html(edu.get('end_date', '')),
                gpa=sanitize_html(edu.get('gpa', '')),
                achievements=sanitize_html(edu.get('achievements', ''))
            )
            db.session.add(education)
        
        # Add experience entries
        for exp in parsed_data.get('experience', []):
            experience = Experience(
                user_profile_id=user_profile.id,
                title=sanitize_html(exp.get('title', '')),
                company=sanitize_html(exp.get('company', '')),
                location=sanitize_html(exp.get('location', '')),
                start_date=sanitize_html(exp.get('start_date', '')),
                end_date=sanitize_html(exp.get('end_date', '')),
                description=sanitize_html(exp.get('description', '')),
                achievements=sanitize_html(exp.get('achievements', ''))
            )
            db.session.add(experience)
        
        # Add skills
        for skill in parsed_data.get('skills', []):
            skill_entry = Skill(
                user_profile_id=user_profile.id,
                name=sanitize_html(skill.get('name', skill if isinstance(skill, str) else '')),
                category=sanitize_html(skill.get('category', '') if isinstance(skill, dict) else ''),
                proficiency=sanitize_html(skill.get('proficiency', '') if isinstance(skill, dict) else '')
            )
            db.session.add(skill_entry)
        
        # Add projects if any
        for proj in parsed_data.get('projects', []):
            project = Project(
                user_profile_id=user_profile.id,
                name=sanitize_html(proj.get('name', '')),
                description=sanitize_html(proj.get('description', '')),
                technologies=sanitize_html(proj.get('technologies', '')),
                url=sanitize_html(proj.get('url', '')),
                achievements=sanitize_html(proj.get('achievements', ''))
            )
            db.session.add(project)
        
        db.session.commit()
        
        logger.info(f"Profile created successfully for session: {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Resume processed and profile created successfully'
        })
    
    except ValueError as e:
        logger.error(f"Value error creating profile: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating profile from resume: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to process resume. Please try again.'}), 500


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
