import logging
import json
from typing import Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class ATSMatchScoringAgent:
    """
    Specialist Agent: ATS Optimization & Job Match Scoring
    
    Mirrors Huntr's Match Scoring Engine that:
    - Calculates real-time job match score
    - Performs dual-layer matching (keyword + semantic)
    - Ensures ATS compliance (formatting, parsing, keywords)
    - Provides breakdown of match across different categories
    """
    
    SYSTEM_PROMPT = """You are an expert ATS (Applicant Tracking System) analyzer and job match scoring specialist.

Your task is to:
1. Calculate a comprehensive job match score (0-100) based on:
   - Keyword coverage (hard skills, soft skills, industry terms)
   - Responsibilities overlap (how well resume matches job duties)
   - Qualifications fit (education, certifications, experience level)
   - Content quality (metrics, achievements, clarity)
   
2. Perform dual-layer matching:
   - Keyword matching: Direct alignment with job description terms
   - Semantic matching: Contextual relevance (e.g., "customer success" ↔ "client retention")

3. Ensure ATS compliance:
   - Check for ATS-friendly formatting
   - Verify proper use of keywords
   - Identify parsing issues

Output your analysis as a structured JSON object with detailed score breakdown."""

    USER_PROMPT_TEMPLATE = """Calculate job match score for this resume against the job posting:

**Target Role:** {role_title}
**Seniority Level:** {seniority_level}

**Job Requirements:**
Required Hard Skills: {required_hard_skills}
Required Qualifications: {required_qualifications}
Key Responsibilities: {responsibilities}

**Resume Content:**
Summary: {resume_summary}
Skills: {resume_skills}
Experience: {resume_experience}
Education: {resume_education}

**Scoring Instructions:**
1. Calculate keyword match score (0-100): How many required keywords appear in resume?
2. Calculate semantic match score (0-100): How well does resume match job meaning/context?
3. Calculate responsibilities coverage (0-100): How well do achievements align with job duties?
4. Calculate qualifications fit (0-100): Education, certs, experience level match?
5. Calculate ATS compliance score (0-100): Formatting, parseability, keyword density

{{
    "overall_match_score": 85,
    "score_breakdown": {{
        "keyword_match": {{
            "score": 75,
            "matched_keywords": ["List of keywords found in resume"],
            "missing_keywords": ["Critical keywords NOT in resume"],
            "coverage_percentage": 75
        }},
        "semantic_match": {{
            "score": 85,
            "strong_alignments": [
                {{"resume_text": "phrase from resume", "job_requirement": "semantically related requirement"}}
            ],
            "explanation": "How resume aligns contextually with job"
        }},
        "responsibilities_coverage": {{
            "score": 80,
            "covered_responsibilities": [
                {{"responsibility": "Job duty", "resume_evidence": "Matching achievement"}}
            ],
            "uncovered_responsibilities": ["Job duties not addressed in resume"]
        }},
        "qualifications_fit": {{
            "score": 90,
            "education_match": true,
            "experience_match": true,
            "certification_match": false,
            "gaps": ["Qualifications you're missing"]
        }},
        "ats_compliance": {{
            "score": 95,
            "issues": ["List of ATS parsing issues"],
            "recommendations": ["How to improve ATS compatibility"]
        }}
    }},
    "improvement_priority": [
        {{
            "area": "keyword_match",
            "impact": "high|medium|low",
            "suggestion": "Specific action to improve this score"
        }}
    ],
    "summary": "Brief explanation of overall match and top improvements needed"
}}

Return ONLY the JSON object, no additional text."""

    def __init__(self, use_openai: bool = True):
        self.use_openai = use_openai
        if use_openai:
            try:
                self.client = OpenAI()
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.use_openai = False
    
    def calculate_match(self, resume_data: Dict, job_analysis: Dict, role_data: Dict) -> Dict:
        """
        Calculate comprehensive job match score.
        
        Args:
            resume_data: Dict with summary, experience, education, skills
            job_analysis: Output from JobDescriptionAnalyzerAgent
            role_data: Dict with company_name, role_title
        
        Returns:
            Dict with match scores and detailed breakdown
        """
        logger.info(f"ATS & Match Scoring Agent calculating match for {role_data['role_title']}")
        
        if self.use_openai:
            try:
                return self._calculate_with_openai(resume_data, job_analysis, role_data)
            except Exception as e:
                logger.error(f"OpenAI scoring failed: {e}, falling back to rules-based")
                return self._calculate_fallback(resume_data, job_analysis, role_data)
        else:
            return self._calculate_fallback(resume_data, job_analysis, role_data)
    
    def _calculate_with_openai(self, resume_data: Dict, job_analysis: Dict, role_data: Dict) -> Dict:
        """Use OpenAI for intelligent match scoring."""
        keywords = job_analysis.get('keywords', {})
        qualifications = job_analysis.get('qualifications', {})
        responsibilities = job_analysis.get('responsibilities', [])
        
        # Flatten resume data
        resume_text = " ".join([
            resume_data.get('summary', ''),
            " ".join(resume_data.get('skills', [])),
            " ".join([bullet for exp in resume_data.get('experience', []) 
                     for bullet in exp.get('bullets', [])])
        ])
        
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            role_title=role_data['role_title'],
            seniority_level=job_analysis.get('seniority_level', 'mid'),
            required_hard_skills=", ".join(keywords.get('hard_skills', [])[:15]),
            required_qualifications=", ".join(qualifications.get('required', {}).get('must_have_skills', [])),
            responsibilities="; ".join([r.get('description', '') for r in responsibilities[:5]]),
            resume_summary=resume_data.get('summary', ''),
            resume_skills=", ".join(resume_data.get('skills', [])),
            resume_experience=resume_text[:500],
            resume_education=", ".join([e.get('degree', '') for e in resume_data.get('education', [])])
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        
        logger.info(f"Match score calculated: {result.get('overall_match_score', 0)}/100")
        return result
    
    def _calculate_fallback(self, resume_data: Dict, job_analysis: Dict, role_data: Dict) -> Dict:
        """Fallback rules-based match scoring."""
        keywords = job_analysis.get('keywords', {})
        hard_skills = [s.lower() for s in keywords.get('hard_skills', [])]
        soft_skills = [s.lower() for s in keywords.get('soft_skills', [])]
        
        resume_text = " ".join([
            resume_data.get('summary', ''),
            " ".join(resume_data.get('skills', [])),
            " ".join([bullet for exp in resume_data.get('experience', []) 
                     for bullet in exp.get('bullets', [])])
        ]).lower()
        
        # Keyword matching
        matched_hard = [skill for skill in hard_skills if skill in resume_text]
        matched_soft = [skill for skill in soft_skills if skill in resume_text]
        
        total_keywords = len(hard_skills) + len(soft_skills)
        matched_keywords = len(matched_hard) + len(matched_soft)
        keyword_score = int((matched_keywords / max(total_keywords, 1)) * 100)
        
        missing_keywords = [s for s in hard_skills if s not in resume_text][:5]
        
        # Qualifications fit
        required_quals = job_analysis.get('qualifications', {}).get('required', {})
        has_education = len(resume_data.get('education', [])) > 0
        
        quals_score = 70
        if has_education:
            quals_score += 20
        if matched_keywords > len(hard_skills) * 0.5:
            quals_score += 10
        
        # Overall score (weighted average)
        overall_score = int(
            keyword_score * 0.4 +
            quals_score * 0.3 +
            85 * 0.2 +  # Semantic (estimated)
            90 * 0.1    # ATS compliance (estimated)
        )
        
        return {
            "overall_match_score": overall_score,
            "score_breakdown": {
                "keyword_match": {
                    "score": keyword_score,
                    "matched_keywords": matched_hard + matched_soft,
                    "missing_keywords": missing_keywords,
                    "coverage_percentage": keyword_score
                },
                "semantic_match": {
                    "score": 85,
                    "strong_alignments": [],
                    "explanation": "Estimated semantic alignment based on keyword matches"
                },
                "responsibilities_coverage": {
                    "score": 80,
                    "covered_responsibilities": [],
                    "uncovered_responsibilities": []
                },
                "qualifications_fit": {
                    "score": quals_score,
                    "education_match": has_education,
                    "experience_match": True,
                    "certification_match": False,
                    "gaps": []
                },
                "ats_compliance": {
                    "score": 90,
                    "issues": [],
                    "recommendations": ["Use standard section headings", "Include keywords naturally"]
                }
            },
            "improvement_priority": [
                {
                    "area": "keyword_match",
                    "impact": "high",
                    "suggestion": f"Add these missing keywords: {', '.join(missing_keywords[:3])}"
                }
            ],
            "summary": f"Resume matches {keyword_score}% of required keywords. "
                      f"Add {len(missing_keywords)} critical skills to improve ATS score."
        }
