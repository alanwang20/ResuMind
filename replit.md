# Resumind - Project Documentation

## Overview
Resumind is an agentic resume and interview preparation tool built with Flask and HTMX. It generates tailored resumes and interview questions based on job descriptions and user experience.

**Status**: MVP Complete and Running  
**Last Updated**: October 30, 2025

## Tech Stack
- **Backend**: Python 3.11, Flask 3.0.3
- **AI**: OpenAI GPT-4o-mini (via Replit AI Integrations)
- **Frontend**: Jinja2 templates, HTMX 1.9.10
- **Styling**: Custom utility CSS (Tailwind-inspired)
- **Session Management**: In-memory storage with UUID-based sessions

## Project Structure
```
/resumind
├── app.py                  # Main Flask application (routes, session management)
├── generators.py           # OpenAI and fallback content generators
├── prompts.py             # AI prompt templates
├── utils.py               # ATS keyword analysis utilities
├── requirements.txt       # Python dependencies
├── README.md             # User-facing documentation
├── static/
│   └── styles.css        # Custom CSS (~200 lines)
└── templates/
    ├── base.html         # Base layout with header/footer
    ├── index.html        # Main input form with HTMX
    └── partial_result.html # Results display (HTMX partial)
```

## Key Features
1. **Tailored Resume Generation**
   - AI-powered resume drafts optimized for job descriptions
   - HTML preview (printable to PDF) and Markdown download
   - Automatic keyword optimization

2. **Interview Prep Questions**
   - 4 behavioral questions (STAR-method friendly)
   - 4 technical/role-specific questions
   - 2 team/organizational fit questions
   - Each with coaching tips

3. **ATS Keyword Analysis**
   - Keyword match report (top matches with counts)
   - Gap analysis (missing keywords from job description)
   - Based on 1-gram and 2-gram extraction

4. **Dual Generator System**
   - Primary: OpenAI API (via Replit AI Integrations)
   - Fallback: Rules-based template generator
   - Automatic fallback on API failure

## OpenAI Integration
- Uses Replit AI Integrations (no API key required)
- Charges billed to Replit credits
- Model: gpt-4o-mini
- Temperature: 0.4 (resume), 0.5 (questions)
- Structured output with XML-like tags for parsing

## Current Workflow
- **Name**: flask-app
- **Command**: `python app.py`
- **Port**: 5000 (webview)
- **Status**: Running

## Environment Variables
- `OPENAI_API_KEY` or `OPENAI_BASE_URL`: Auto-configured by Replit AI Integrations
- `SESSION_SECRET`: Flask session secret (auto-generated)

## Session Management
- In-memory Python dict storage
- UUID-based session IDs
- No database persistence (privacy-first design)
- Sessions cleared on server restart

## Input Limits
- Max field length: 20,000 characters
- Max file upload: 25 MB
- Supported file format: .txt

## Recent Changes
**October 30, 2025**
- Initial MVP implementation
- Created all core files (app.py, generators.py, prompts.py, utils.py)
- Implemented HTMX-based UI with partial updates
- Added ATS keyword matching algorithm
- Configured Replit AI Integrations for OpenAI
- Set up Flask workflow on port 5000

## User Preferences
None specified yet.

## Privacy & Security
- No data persistence - all processing in memory
- No user data stored on server
- Session data temporary (cleared on page refresh)
- Basic input sanitization and length limits

## Next Steps (Future Enhancements)
1. RAG integration over high-performing resume corpus
2. Resume template variations with A/B testing
3. Outcome tracking ("got interview?" feedback)
4. User authentication and saved resume versions
5. PostgreSQL persistence for resume history
6. Advanced ATS analysis with deeper insights
7. LinkedIn profile import for auto-extraction

## Development Notes
- LSP diagnostics: Currently 2 minor import warnings in app.py (false positives after package installation)
- All core functionality tested and working
- HTMX provides smooth partial page updates without full reloads
- Fallback generator ensures app works without AI access
