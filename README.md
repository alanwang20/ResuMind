<div align="center">

# ResuMind
### *Agentic Resume Intelligence*

**Upload once. Tailor infinitely.**  
AI-powered resume optimization using six specialized agents working in parallel.

---

</div>

## 🎯 Long-Term Vision

The long-term goal for ResuMind is to evolve from a resume-tailoring prototype into a **personal career copilot**—an adaptive agent that grows alongside the user.

Instead of static resume edits, ResuMind will learn over time which narratives resonate with specific companies, industries, and recruiters, shaping both what users say and how they present it.

Ultimately, the system would become an **autonomous career agent** capable of searching roles, aligning application materials, generating personalized simulations, and learning from outcomes—a closed-loop AI that helps people tell their professional story with clarity, confidence, and precision.

---

## 🚀 What It Does Right Now

ResuMind is an **upload-first resume crafting system** powered by six specialized AI agents:

### **Upload → Parse → Tailor**

1. **Upload your resume** (PDF, DOCX, or TXT)
2. **Auto-parse and store** your education, experience, skills, and projects
3. **Enter job details** for the role you're applying to
4. **Get a tailored resume** optimized for that specific job with real-time ATS scoring (0-100)

---

## 🧠 The Six Specialist Agents

ResuMind uses a Huntr.co-inspired **parallel multi-agent architecture** where each agent specializes in one task:

1. **Resume Parser Agent**  
   Extracts structured data from your uploaded resume (education, work history, skills, projects)

2. **Job Description Analyzer Agent**  
   Parses job postings to identify key requirements, keywords, and company tone

3. **Content Optimizer Agent**  
   Rewrites bullet points to match job requirements while maintaining authenticity

4. **ATS Match Scoring Agent**  
   Provides real-time 0-100 scoring for keyword optimization and ATS compatibility

5. **Proofreading & Quality Agent**  
   Catches grammar issues, improves clarity, and ensures professional tone

6. **Role Calibration Agent**  
   Ranks your experiences by relevance and tailors presentation for the specific role

All agents work **in parallel** for speed, with intelligent fallbacks when AI is unavailable.

---

## ⚡ Key Features

- **Upload-First Workflow** – Parse your resume automatically, no manual data entry
- **Real-Time ATS Scoring** – See how well your resume matches the job (0-100 scale)
- **Keyword Optimization** – Automatically identify and optimize for job-specific terms
- **Multi-Agent Intelligence** – Six specialists working together for superior results
- **Graceful Fallbacks** – Works even without OpenAI using regex-based parsing
- **Privacy-First** – Your data stays local in SQLite, you control it
- **Session-Based** – Upload once, generate tailored resumes for multiple jobs

---

## 🛠️ Tech Stack

- **Backend:** Python 3.11 + Flask 3.0.3
- **Database:** SQLite with SQLAlchemy ORM
- **AI:** OpenAI GPT-4 (optional, with intelligent fallbacks)
- **Parsing:** PyPDF2, python-docx
- **Security:** Bleach HTML sanitization, parameterized queries

---

## 📦 Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure OpenAI (Optional)

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
SESSION_SECRET=your-random-secret-key
```

**Getting an OpenAI API Key:**
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)
5. Paste it into your `.env` file

**Note:** The OpenAI API key is **optional**. Without it, ResuMind uses a robust regex-based fallback parser that works great for most resumes.

### 3. Run the Application

```bash
python app.py
```

The app will start on `http://0.0.0.0:5000`

---

## 📁 Project Structure

```
resumind/
├── app.py                          # Main Flask application
├── models/
│   ├── __init__.py                 # Database instance
│   └── user_profile.py             # User, Education, Experience, Skills, Projects
├── services/
│   ├── orchestration.py            # Multi-agent coordinator
│   └── agents/                     # Six specialist agents
│       ├── resume_parser_agent.py
│       ├── job_description_analyzer_agent.py
│       ├── content_optimizer_agent.py
│       ├── ats_match_scoring_agent.py
│       ├── proofreading_quality_agent.py
│       └── role_calibration_agent.py
├── templates/                      # HTML templates
├── static/                         # CSS and assets
└── requirements.txt
```

---

## 🧪 Lessons Learned (First Agentic AI Experiment)

This project was my first experiment using Replit and Agentic AI. Here are the key takeaways:

### 1. **Start Simple — Multi-Agent Systems Are Hard**
Building multiple agents from the start was much harder than expected. If I were to do it again, I'd perfect each agent individually (reader → extractor → aligner) before layering in orchestration.

### 2. **Less Abstraction, More Control**
Higher-level frameworks are convenient, but dropping down a level (custom orchestration) gives you control over how agents communicate and share context.

### 3. **Prompt Engineering Is Everything**
Small changes in phrasing or instruction structure drastically improve coherence, formatting, and accuracy.

### 4. **Pay for OpenAI Credits** 😅
Limited access = limited debugging ability. Without sufficient tokens, it's hard to test complex agent interactions.

### 5. **State and Memory Management Are Crucial**
Multi-agent systems break easily without clear shared memory or context handoff. Even a lightweight state layer helps maintain continuity.

### 6. **Orchestration Is the Real Product**
The "glue"—sequencing, error handling, feedback loops—matters more than the agents themselves. Success comes from building a reliable orchestrator.

### 7. **Evaluation and Ground Truth Matter**
It's difficult to tell if an agent succeeded without metrics. Future iterations should have structured benchmarks before spending time on prompt tuning.

### 8. **Cost and Context Optimization**
Combining resumes, job descriptions, and reasoning prompts quickly blows up token counts. Smaller, modular prompts and cached embeddings make this cheaper and faster.

### 9. **UI ≠ Workflow**
Designing the UI first exposed a sync problem—the backend logic and agent flow need to be stable before connecting to the front end.

### 10. **Privacy and Data Handling**
Since this involves personal resumes and job data, build with data privacy and local storage in mind. Logs and caches can unintentionally expose sensitive info.

### 11. **Reliability > Intelligence**
The first goal isn't to make the smartest agent—it's to make the most dependable one. Perfecting one agent before chaining many is the real foundation for autonomous AI systems.

---

## 🔮 Next Steps (Roadmap)

### Phase 1: Modularization & Testing
- ✅ Break the monolith into smaller, testable agents
- ✅ Implement upload-first workflow with auto-parsing
- 🔄 Add evaluation metrics for each agent (skill extraction accuracy, keyword comprehension, alignment quality)

### Phase 2: Advanced Orchestration
- Introduce a **Central Workflow Orchestrator** with self-correction when outputs conflict
- Add **structured memory layer** (Redis or vector database) to cache embeddings and retain context
- Implement **RAG (Retrieval-Augmented Generation)** with real anonymized resumes and company culture data

### Phase 3: Intelligent Iteration
- Build **prompt iteration framework** to rapidly test and compare variants
- Expand UI into **guided conversation** ("Can you describe your leadership outcome in that project?")
- Add **"view what the AI saw"** feature for transparency

### Phase 4: Self-Improving Agents
- Let the orchestrator **learn from results** (Resume A got an interview, B didn't → update scoring heuristics)
- Track which resume versions get interviews
- Implement A/B testing for continuous improvement

### Phase 5: Production MVP
- Deploy to **Vercel or AWS Lambda + RDS (Postgres)**
- Add **user authentication** for resume history
- Connect **analytics dashboard** to measure engagement and success rates
- Implement **PDF export** (currently print to PDF)
- Add **LinkedIn import** to auto-populate profiles

---

## 🔒 Privacy & Security

- **HTML Sanitization:** All user and AI-generated content is sanitized before storage
- **SQL Injection Protection:** Parameterized queries via SQLAlchemy ORM
- **Local Storage:** Your resume data stays in your SQLite database
- **No External Tracking:** Only OpenAI API calls when AI is enabled (can be disabled)

---

## 🤝 Contributing

This is a personal experiment, but ideas and feedback are welcome! Feel free to fork and adapt for your own use.

---

## 📄 License

For personal use. Built for job seekers everywhere.

---

<div align="center">

**ResuMind** – *Where intelligence meets opportunity*

</div>
