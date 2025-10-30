# ResuMind

> **AI-Powered Resume Tailoring for the Modern Job Seeker**

ResuMind is a multi-agent resume crafting system that automatically parses your resume and generates perfectly tailored versions for any job posting—powered by six specialized AI agents working in parallel.

## What is Resumind?

Resumind revolutionizes resume creation by analyzing company preferences and tailoring your experiences to match specific job requirements. Unlike generic resume builders, Resumind uses specialized AI agents to understand what each company values and optimizes your resume accordingly.

## How It Works

### Three Specialized AI Agents

1. **Company Insight Agent**
   - Analyzes the job posting and company information
   - Identifies company-specific resume preferences (e.g., "Google prefers quantifiable impact metrics")
   - Extracts key requirements and important keywords
   - Detects tone and formatting expectations

2. **Experience Summarizer Agent**
   - Converts your raw profile data into structured accomplishment summaries
   - Highlights quantifiable metrics and impact
   - Identifies transferable skills relevant to the role
   - Uses strong action verbs and achievement-focused language

3. **Alignment Agent**
   - Matches your experiences to the specific role requirements
   - Ranks experiences by relevance to the position
   - Tailors bullet points to company preferences and keywords
   - Ensures ATS (Applicant Tracking System) optimization

### Two-Step Process

**Step 1: Build Your Profile**
Enter your comprehensive professional profile once:
- Personal information (name, contact, LinkedIn, portfolio)
- Education history with GPA and achievements
- Work experiences with detailed accomplishments
- Technical and soft skills
- Projects and side work

**Step 2: Target a Role**
For each job application, provide:
- Company name
- Role title
- Complete job description (paste from posting)
- Optional: Company culture notes or additional information

**Step 3: Get Your Tailored Resume**
Resumind generates:
- A customized resume optimized for the specific role
- Keyword coverage analysis showing ATS optimization
- Agent insights explaining tailoring decisions
- Both HTML preview and Markdown download

## Key Features

- **Multi-Agent Intelligence**: Three specialized AI agents work together for superior results
- **ATS Optimization**: Automatic keyword matching and coverage analysis
- **Company-Specific Tailoring**: Detects and adapts to company resume preferences
- **Session-Based Storage**: Save your profile, generate multiple tailored resumes
- **Reusable Profiles**: Enter your information once, use it for many applications
- **Secure & Private**: HTML sanitization, local database, your data stays with you
- **Fallback Mode**: Works even without AI, using intelligent rule-based generation

## Technology Stack

- **Backend**: Python 3.11 + Flask 3.0.3
- **Database**: SQLite with SQLAlchemy ORM
- **AI**: OpenAI GPT-4o-mini (via Replit AI Integrations)
- **Frontend**: Jinja2 templates + vanilla JavaScript
- **Security**: Bleach HTML sanitization

## Getting Started

### On Replit (Recommended)

The app uses Replit AI Integrations for OpenAI access (no API key needed - charges are billed to your Replit credits).

1. The integration is already configured in this project
2. Dependencies are automatically installed
3. Click "Run" or execute:
   ```bash
   python app.py
   ```
4. Access at the provided webview URL

### Using Your Own OpenAI API Key (Optional)

If you prefer to use your own OpenAI API key:

1. Add `OPENAI_API_KEY` to your Replit Secrets
2. The app will automatically use it instead of the Replit integration

### Fallback Mode

If no OpenAI access is available, the app automatically falls back to rule-based generation that still produces functional resumes.

## Usage

1. **Create Your Profile**
   - Visit the homepage and fill out the comprehensive profile form
   - Include as much detail as possible for better results
   - Add multiple education entries, experiences, skills, and projects

2. **Target a Specific Role**
   - After saving your profile, you'll be redirected to the role form
   - Paste the complete job description
   - Add any additional company information you know

3. **Review Your Tailored Resume**
   - View the HTML preview of your customized resume
   - Check the keyword coverage analysis
   - Read agent insights to understand tailoring decisions
   - Download the Markdown version

4. **Apply with Confidence**
   - Use the tailored resume for your application
   - Repeat steps 2-3 for each new job posting

## Database Schema

The application stores:
- **UserProfile**: Your personal and professional information
- **Education**: Academic history with achievements
- **Experience**: Work history with accomplishments
- **Skill**: Technical and soft skills with proficiency levels
- **Project**: Side projects and portfolio work
- **RoleSubmission**: Each tailored resume with cached agent outputs

All data is stored locally in `resumind.db` and persists across sessions.

## Security Features

- **HTML Sanitization**: All user and AI-generated content is sanitized before storage
- **Input Validation**: Form data validated before database insertion
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy ORM
- **Session Security**: Secure server-side sessions
- **Privacy-First**: Your data stays local, you control it

## Project Structure

```
/resumind
├── app.py                          # Main Flask application
├── models/
│   ├── __init__.py                 # Database instance
│   └── user_profile.py             # ORM models
├── services/
│   ├── orchestration.py            # Agent coordinator
│   └── agents/
│       ├── company_insight_agent.py
│       ├── experience_summarizer_agent.py
│       └── alignment_agent.py
├── templates/
│   ├── base.html
│   ├── profile_form.html           # Step 1: Profile input
│   ├── role_form.html              # Step 2: Role targeting
│   ├── resume_result.html          # Results display
│   └── error.html
├── static/
│   └── styles.css
├── utils.py                        # Keyword utilities
└── requirements.txt
```

## Why Multi-Agent?

Traditional resume builders use templates or single AI prompts. Resumind's multi-agent approach provides:

1. **Specialization**: Each agent focuses on one task it does extremely well
2. **Better Analysis**: Company preferences are analyzed separately from experience summarization
3. **Explainability**: See what each agent detected and decided
4. **Reliability**: If one agent fails, others continue; fallback mode ensures results
5. **Quality**: Multiple passes of refinement produce superior resumes

## Next Steps

Potential enhancements:

- **User Authentication**: Multi-user support with login
- **Resume History**: View and compare previous tailored resumes
- **Template Selection**: Multiple resume formats and styles
- **PDF Export**: Direct PDF generation (currently print to PDF)
- **Company Database**: Pre-populated company preference knowledge
- **Resume Scoring**: ATS compatibility score with improvement suggestions
- **A/B Testing**: Track which resume versions get interviews
- **LinkedIn Import**: Auto-populate profile from LinkedIn
- **Cover Letter Generation**: Additional agent for cover letters
- **Real-time Collaboration**: Share resumes with mentors/friends

## Privacy

Your professional profile and resume data are stored locally in the SQLite database. No information is sent to external services except OpenAI API calls for AI-powered generation (which can be disabled by running in fallback mode).

## Running Locally (After Download)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
SESSION_SECRET=your-random-secret-key
```

**Getting an OpenAI API Key:**
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with "sk-...")
5. Paste it into your `.env` file

### 3. Run the Application

```bash
python app.py
```

The app will start on `http://0.0.0.0:5000`

**Note:** The OpenAI API key is optional. If you don't provide it, the app will use the fallback regex-based parser which still works great for most resumes!

## License

Built with ❤️ for job seekers everywhere.
