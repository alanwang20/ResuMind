# Resumind - Multi-Agent Resume Crafting System

## Overview
Resumind is a sophisticated multi-agent system that crafts tailored resumes mirroring Huntr.co's processing structure. Features 6 specialized AI agents running in parallel, real-time job match scoring (0-100), and upload-first workflow. Built with Flask, SQLAlchemy, and OpenAI.

**Status**: MVP Complete - Upload-First Flow Active  
**Last Updated**: October 30, 2025

## Architecture

### Huntr.co-Style Multi-Agent System
The application uses 6 specialized AI agents running in parallel via ThreadPoolExecutor:

1. **Job Description Analyzer** (`services/agents/job_description_analyzer_agent.py`)
   - Extracts key skills, qualifications, and requirements from job postings
   - Identifies technical skills, soft skills, certifications, and experience requirements
   - Analyzes company culture and role-specific keywords
   - Provides structured JSON output for matching

2. **Content Optimizer** (`services/agents/content_optimizer_agent.py`)
   - Optimizes resume content for job-specific language
   - Rewrites bullet points with strong action verbs
   - Quantifies achievements and adds metrics
   - Ensures professional tone and clarity

3. **ATS & Match Scoring** (`services/agents/ats_match_scoring_agent.py`)
   - Real-time job match score calculation (0-100)
   - Detailed scoring breakdown: keywords, qualifications, ATS compliance, semantic fit
   - Identifies missing keywords and qualification gaps
   - Provides actionable improvement recommendations

4. **Proofreading & Quality** (`services/agents/proofreading_quality_agent.py`)
   - Grammar and spelling verification
   - Consistency checking (dates, formatting, tense)
   - Professional language review
   - Final quality assurance before output

5. **Role Calibration** (`services/agents/role_calibration_agent.py`)
   - Adjusts resume tone for seniority level and role type
   - Customizes content emphasis based on job requirements
   - Ensures experience relevance and appropriate depth
   - Calibrates technical vs. soft skill balance

6. **Resume Parser Agent** (`services/agents/resume_parser_agent.py`)
   - Extracts structured information from uploaded resume files
   - Parses PDF, DOCX, and TXT formats
   - Uses OpenAI to intelligently extract: personal info, education, experience, skills, projects
   - Fallback uses regex and keyword extraction for basic parsing
   - Auto-creates user profile in database

7. **Resume Orchestrator** (`services/orchestration.py`)
   - Coordinates all 6 specialist agents in parallel
   - Uses ThreadPoolExecutor for concurrent agent execution
   - Synthesizes results into final tailored resume
   - Provides detailed agent insights and debugging info
   - Handles fallback to rules-based generation if AI unavailable

### Data Flow (Upload-First)

```
Landing Page: Upload Resume (PDF/DOCX/TXT)
    ↓
Resume Parser Agent: Extract structured data
    ↓
Database: Auto-create user profile
    ↓
Role Input Page: Enter job description
    ↓
6 Agents Run in Parallel:
  - Job Description Analyzer
  - Content Optimizer
  - ATS & Match Scoring
  - Proofreading & Quality
  - Role Calibration
  - (Resume Parser - already complete)
    ↓
Orchestrator: Synthesize all agent outputs
    ↓
Display: Tailored Resume + Match Score (0-100) + Agent Insights
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

## User Flow (Upload-First)

### Step 1: Upload Resume
- Beautiful drag-and-drop landing page
- Supports PDF, DOCX, or TXT files (max 25MB)
- AI automatically parses and extracts all information
- Profile created in database automatically
- Seamless redirect to job targeting

### Step 2: Role Targeting
User provides:
- Target company name
- Role title
- Complete job description (paste)
- Optional: Additional company culture/preference information

### Step 3: Parallel Multi-Agent Processing
System runs 6 agents in parallel via ThreadPoolExecutor:
1. Job Description Analyzer → Extract requirements and keywords
2. Content Optimizer → Rewrite and enhance bullet points
3. ATS & Match Scoring → Calculate match score (0-100)
4. Proofreading & Quality → Grammar and consistency check
5. Role Calibration → Adjust tone for seniority and role type
6. Resume synthesis and final assembly

All outputs cached in database for audit trail.

### Step 4: Results
User receives:
- Tailored resume (HTML preview + Markdown download)
- Real-time job match score (0-100) with detailed breakdown
- Missing keywords and qualification gaps
- Agent insights (job analysis, optimization notes, quality feedback)
- Actionable improvement recommendations

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

**October 30, 2025 - Upload-First Flow Implementation**
- Redesigned landing page to upload-first workflow (removed manual form entry)
- Created `/upload_and_create_profile` endpoint for seamless resume upload → profile creation
- Auto-creates user profile directly from parsed resume data
- Eliminated manual form filling step entirely
- Redirect flow: upload → parse → auto-create profile → job input
- Cleaned up unused template files (profile_form.html removed)
- Simplified user experience: 2 steps instead of 3

**October 30, 2025 - Huntr.co-Style Multi-Agent Architecture**
- Complete redesign to mirror Huntr.co's parallel processing structure
- Implemented 6 specialized agents: Job Analyzer, Content Optimizer, ATS Scoring, Proofreading, Role Calibration, Resume Parser
- Parallel agent execution via ThreadPoolExecutor for speed
- Real-time job match scoring (0-100) with detailed breakdown
- Keyword gap analysis and qualification matching
- Added structured defaults and backward compatibility to prevent UI breakage
- Removed old agents (alignment_agent, company_insight_agent, experience_summarizer_agent)

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
