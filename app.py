import os
import uuid
import logging
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
import io
import markdown
import bleach

from generators import generate_with_openai, generate_fallback
from utils import truncate_log

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024

sessions = {}

MAX_FIELD_LENGTH = 20000


def sanitize_input(text: str, max_length: int = MAX_FIELD_LENGTH) -> str:
    """Basic input sanitization and length limiting."""
    if not text:
        return ""
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    return text


@app.route('/')
def index():
    """Main page with input form."""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """Generate resume and interview prep materials."""
    try:
        job_description = request.form.get('job_description', '')
        user_experience = request.form.get('user_experience', '')
        
        uploaded_file = request.files.get('resume_file')
        if uploaded_file and uploaded_file.filename:
            try:
                file_content = uploaded_file.read().decode('utf-8')
                if user_experience:
                    user_experience += '\n\n' + file_content
                else:
                    user_experience = file_content
            except Exception as e:
                logger.warning(f"Could not read uploaded file: {e}")
        
        job_description = sanitize_input(job_description)
        user_experience = sanitize_input(user_experience)
        
        if not job_description or not user_experience:
            return render_template('partial_result.html', 
                                 error="Please provide both job description and experience."), 400
        
        logger.info(f"Generate request - Job desc: {len(job_description)} chars, Experience: {len(user_experience)} chars")
        
        payload = {
            'job_description': job_description,
            'user_experience': user_experience
        }
        
        session_id = str(uuid.uuid4())
        
        openai_available = os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_BASE_URL')
        
        try:
            if openai_available:
                logger.info("Using OpenAI generator")
                result = generate_with_openai(payload)
            else:
                logger.warning("OPENAI_API_KEY not found, using fallback generator")
                result = generate_fallback(payload)
        except Exception as e:
            logger.error(f"OpenAI generation failed, falling back: {e}")
            result = generate_fallback(payload)
        
        sessions[session_id] = result
        
        questions_html = markdown.markdown(result['questions_md'])
        questions_html = bleach.clean(
            questions_html,
            tags=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'strong', 'em', 'u', 'b', 'i', 'ul', 'ol', 'li'],
            attributes={},
            strip=True
        )
        
        return render_template('partial_result.html',
                             session_id=session_id,
                             resume_html=result['resume_html'],
                             questions_html=questions_html,
                             ats_report=result['ats_report'])
    
    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        return render_template('partial_result.html', 
                             error=f"An error occurred: {str(e)}"), 500


@app.route('/download/<kind>/<session_id>')
def download(kind, session_id):
    """Download markdown files."""
    if session_id not in sessions:
        return "Session not found", 404
    
    result = sessions[session_id]
    
    if kind == 'resume':
        content = result.get('resume_md', '')
        filename = 'resume.md'
    elif kind == 'questions':
        content = result.get('questions_md', '')
        filename = 'interview_questions.md'
    else:
        return "Invalid download type", 400
    
    return Response(
        content,
        mimetype='text/markdown',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
