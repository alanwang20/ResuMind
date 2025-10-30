# Resumind

An agentic resume and interview prep tool built with Flask and HTMX.

## Features

- **Tailored Resume Generation**: AI-powered resume drafts optimized for specific job descriptions
- **Interview Prep Questions**: Behavioral, technical, and team-fit questions with coaching tips
- **ATS Keyword Analysis**: Match report showing keyword alignment and gaps
- **Export Options**: Download resumes and questions in Markdown format, print to PDF
- **Privacy-First**: No data persistence - everything runs in memory

## Setup

### On Replit (Recommended)

The app uses Replit AI Integrations for OpenAI access (no API key needed - charges are billed to your Replit credits).

1. The integration is already configured in this project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Access at `http://localhost:5000`

### Using Your Own OpenAI API Key (Optional)

If you prefer to use your own OpenAI API key:

1. Add `OPENAI_API_KEY` to your Replit Secrets
2. The app will automatically use it instead of the Replit integration

### Fallback Mode

If no OpenAI access is available, the app automatically falls back to a rules-based generator that still produces functional resumes and interview questions.

## Usage

1. **Paste Job Description**: Copy the job posting you're targeting
2. **Add Your Experience**: Type or upload your resume/experience as a text file
3. **Generate**: Click the button to create:
   - Tailored resume (HTML preview + Markdown download)
   - Interview prep questions (Markdown download)
   - ATS keyword match report

4. **Export**: 
   - Print the resume preview to PDF using your browser (Ctrl/Cmd + P)
   - Download Markdown files for editing

## Tech Stack

- **Backend**: Python 3.11, Flask 3.0.3
- **AI**: OpenAI GPT-4o-mini (via Replit AI Integrations)
- **Frontend**: Jinja2 templates, HTMX for dynamic updates
- **Styling**: Custom utility CSS (Tailwind-inspired)
- **Session Management**: In-memory storage with UUIDs

## Project Structure

```
/resumind
  ├─ app.py                 # Flask application and routes
  ├─ prompts.py            # AI prompt templates
  ├─ generators.py         # OpenAI and fallback generators
  ├─ utils.py              # ATS analysis and utilities
  ├─ requirements.txt      # Python dependencies
  ├─ static/
  │   └─ styles.css        # Custom CSS
  └─ templates/
      ├─ base.html         # Base layout
      ├─ index.html        # Main form
      └─ partial_result.html  # Results display
```

## Next Steps

Potential enhancements:

- **RAG Integration**: Add retrieval over high-performing resume corpus
- **Template Variations**: A/B test different resume formats
- **Outcome Tracking**: "Did you get an interview?" feedback loop
- **User Authentication**: Save multiple resume versions
- **Database Persistence**: Store resumes and track improvements
- **Advanced ATS**: Deeper keyword analysis and optimization suggestions

## Notes

- Maximum input length: 20,000 characters per field
- Session data is temporary and cleared when the page is refreshed
- For best PDF export results, use Chrome or Edge browser
- The fallback generator uses keyword extraction and templates when AI is unavailable

## Privacy

This MVP processes all data in memory and does not persist user information. Your job descriptions and experience are only stored temporarily during your session.
