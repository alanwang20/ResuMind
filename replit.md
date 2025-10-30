# Resumind - Multi-Agent Resume Crafting System

## Overview
Resumind is a sophisticated multi-agent system that crafts tailored resumes by analyzing company preferences and matching user experiences to specific job postings. Built with Flask, SQLAlchemy, and OpenAI.

**Status**: MVP Complete - Multi-Agent System Active  
**Last Updated**: October 30, 2025

## Architecture

### Multi-Agent System
The application uses three specialized AI agents coordinated by an orchestrator:

1. **Company Insight Agent** (`services/agents/company_insight_agent.py`)
   - Analyzes job postings and company information
   - Extracts company-specific resume preferences (e.g., "Big tech prefers 1-2 word bullet starts")
   - Identifies key requirements and important keywords
   - Detects tone and formatting expectations

2. **Experience Summarizer Agent** (`services/agents/experience_summarizer_agent.py`)
   - Converts raw user profile data into structured accomplishment summaries
   - Extracts key achievements with quantifiable metrics
   - Highlights transferable skills and impact areas
   - Uses strong action verbs

3. **Alignment Agent** (`services/agents/alignment_agent.py`)
   - Matches user experiences to specific role requirements
   - Ranks experiences by relevance
   - Tailors bullet points to company preferences and keywords
   - Ensures ATS optimization with keyword coverage

4. **Resume Orchestrator** (`services/orchestration.py`)
   - Coordinates all three agents in sequence
   - Handles fallback to rules-based generation if AI unavailable
   - Logs agent decisions and timing
   - Provides debugging information

### Data Flow

```
Page 1: User Profile Input
    ↓
Database: Store complete profile
    ↓
Page 2: Role & Company Input
    ↓
Agent 1: Analyze Company → Company Insights
    ↓
Agent 2: Summarize Profile → Experience Summaries
    ↓
Agent 3: Align & Tailor → Tailored Resume HTML/MD + Keyword Coverage
    ↓
Display: Resume Preview + ATS Analysis + Agent Insights
```

## Tech Stack
- **Backend**: Python 3.11, Flask 3.0.3
- **Database**: SQLite with SQLAlchemy 2.0.30
- **AI**: OpenAI GPT-4o-mini (via Replit AI Integrations)
- **Frontend**: Jinja2 templates, vanilla JavaScript
- **Styling**: Custom utility CSS (~470 lines)
- **Security**: Bleach HTML sanitization, input validation

## Project Structure
```
/resumind
├── app.py                          # Main Flask application (two-page flow)
├── models/
│   ├── __init__.py                 # SQLAlchemy db instance
│   └── user_profile.py             # ORM models (UserProfile, Education, Experience, etc.)
├── services/
│   ├── __init__.py
│   ├── orchestration.py            # ResumeOrchestrator (coordinates agents)
│   └── agents/
│       ├── __init__.py
│       ├── company_insight_agent.py    # Agent 1: Company analysis
│       ├── experience_summarizer_agent.py # Agent 2: Profile summarization
│       └── alignment_agent.py          # Agent 3: Resume tailoring
├── templates/
│   ├── base.html                   # Base layout
│   ├── profile_form.html           # Page 1: Profile input
│   ├── role_form.html              # Page 2: Role/company input
│   ├── resume_result.html          # Results display
│   └── error.html                  # Error page
├── static/
│   └── styles.css                  # Enhanced CSS with form styles
├── utils.py                        # ATS keyword utilities
└── requirements.txt                # Python dependencies
```

## Database Schema

### UserProfile
- Basic info: name, email, phone, location, linkedin, website
- Professional summary
- Session-based identification (UUID)
- Relationships to: Education, Experience, Skills, Projects, RoleSubmissions

### Education
- Degree, field of study, institution, location
- Start/end dates, GPA, achievements

### Experience
- Title, company, location, dates, current flag
- Description and achievements

### Skill
- Name, category (e.g., "Programming Languages"), proficiency

### Project
- Name, description, technologies, URL
- Achievements and impact

### RoleSubmission
- Company name, role title, job description, company info
- Cached agent outputs: company_insights, experience_summaries, aligned_resume
- Timestamp for tracking

## User Flow

### Step 1: Profile Creation
User enters comprehensive profile information:
- Personal details (name, contact, links)
- Education history (with GPA, achievements)
- Work experiences (with achievements)
- Skills (categorized, with proficiency)
- Projects (optional, with technologies)

Data is validated and stored in SQLite database with unique session ID.

### Step 2: Role Targeting
User provides:
- Target company name
- Role title
- Complete job description (paste)
- Optional: Additional company culture/preference information

### Step 3: Multi-Agent Generation
System runs three agents in sequence:
1. Analyzes company preferences → Company Insights JSON
2. Summarizes user profile → Experience Summaries JSON
3. Aligns and tailors → Resume HTML/MD + Keyword Coverage

All outputs cached in database for audit trail.

### Step 4: Results
User receives:
- Tailored resume (HTML preview + Markdown download)
- Keyword coverage analysis (covered vs. emphasized)
- Agent insights (company preferences detected, tailoring notes)
- Next steps guidance

## OpenAI Integration
- Uses Replit AI Integrations (no API key required)
- Charges billed to Replit credits
- Models: gpt-4o-mini (all agents)
- Temperature: 0.3-0.4 for deterministic outputs
- JSON response format for structured outputs
- Automatic fallback to rules-based generation

## Security & Privacy
- **HTML Sanitization**: All user-generated and AI-generated HTML sanitized with bleach
- **Input Validation**: Form data validated before database insertion
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **Session Management**: Server-side sessions with secure secret key
- **Data Persistence**: Database stored locally (resumind.db)
- **Privacy**: User controls their data, can create multiple profiles

## Workflow
- **Name**: flask-app
- **Command**: `python app.py`
- **Port**: 5000 (webview)
- **Status**: Running

## Environment Variables
- `OPENAI_API_KEY` or `OPENAI_BASE_URL`: Auto-configured by Replit AI Integrations
- `SESSION_SECRET`: Flask session secret

## Agent Fallback Modes
Each agent has a rules-based fallback:

**Company Insight Fallback**:
- Keyword extraction via n-grams
- Big tech detection (Google, Meta, Amazon, etc.)
- Predefined formatting rules

**Experience Summarizer Fallback**:
- Bullet point extraction from user text
- Action verb prepending
- Skill categorization

**Alignment Fallback**:
- Template-based resume generation
- HTML escaping for security
- Keyword matching for coverage analysis

## Recent Changes
**October 30, 2025 - Multi-Agent System Implementation**
- Complete architectural redesign from single-shot to multi-agent system
- Created three specialized AI agents with orchestration
- Implemented two-page data collection flow
- Added SQLAlchemy database with comprehensive schema
- Enhanced security with HTML sanitization throughout
- Added keyword coverage analysis and agent insights
- Removed interview questions feature (focus on resume crafting)
- Created dynamic form UI with add/remove fields
- Implemented session-based multi-submission support

## User Preferences
None specified yet.

## Next Steps (Future Enhancements)
1. **User Authentication**: Multi-user support with login
2. **Resume History**: View and compare previous tailored resumes
3. **Template Selection**: Multiple resume formats and styles
4. **Export Options**: PDF generation, Word export
5. **Company Database**: Pre-populated company preference knowledge
6. **Resume Scoring**: ATS compatibility score with improvement suggestions
7. **A/B Testing**: Track which resume versions get interviews
8. **LinkedIn Import**: Auto-populate profile from LinkedIn
9. **Cover Letter Generation**: Additional agent for cover letters
10. **Real-time Collaboration**: Share resumes with mentors/friends

## Development Notes
- LSP diagnostics: 10 minor issues (mostly type hints, non-blocking)
- All core functionality tested and working
- Multi-agent coordination successful
- Fallback modes operational
- Database migrations handled automatically via db.create_all()

## Debugging Endpoints
- `/agent_status`: Check which agents are using OpenAI vs. fallback mode
