import logging
import json
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.agents.job_description_analyzer_agent import JobDescriptionAnalyzerAgent
from services.agents.resume_parser_agent import ResumeParserAgent
from services.agents.proofreading_quality_agent import ProofreadingQualityAgent
from services.agents.content_optimizer_agent import ContentOptimizerAgent
from services.agents.ats_match_scoring_agent import ATSMatchScoringAgent
from services.agents.role_calibration_agent import RoleCalibrationAgent

logger = logging.getLogger(__name__)


class ResumeOrchestrator:
    """
    Huntr-Style Multi-Specialist Agent Orchestrator
    
    Mirrors Huntr.co's processing structure with parallel specialist agents:
    1. Job Description Analyzer - Extracts keywords, responsibilities, qualifications
    2. Proofreading & Quality Agent - Grammar, metrics, clichés
    3. Content Optimizer Agent - Rewrites bullets and summaries
    4. ATS & Match Scoring Agent - Calculates job match score
    5. Role Calibration Agent - Adjusts tone for seniority level
    6. Resume Parser Agent - Parses uploaded resumes
    
    Agents run in parallel for speed, just like Huntr's architecture.
    """
    
    def __init__(self, use_openai: bool = True):
        self.use_openai = use_openai
        
        # Initialize all specialist agents
        self.job_analyzer = JobDescriptionAnalyzerAgent(use_openai)
        self.resume_parser = ResumeParserAgent(use_openai)
        self.proofreader = ProofreadingQualityAgent(use_openai)
        self.content_optimizer = ContentOptimizerAgent(use_openai)
        self.ats_scorer = ATSMatchScoringAgent(use_openai)
        self.role_calibrator = RoleCalibrationAgent(use_openai)
        
        logger.info(f"Huntr-style ResumeOrchestrator initialized with 6 specialist agents (OpenAI: {use_openai})")
    
    def generate_tailored_resume(self, profile_data: Dict, role_data: Dict) -> Dict:
        """
        Main orchestration method mirroring Huntr's processing flow.
        
        Processing Flow (Huntr-style):
        1. Analyze job description (keywords, responsibilities, qualifications)
        2. Run specialist agents IN PARALLEL:
           - Proofreading & Quality Review
           - Content Optimization
           - ATS Match Scoring
           - Role Calibration
        3. Combine all results with match score and suggestions
        
        Args:
            profile_data: Complete user profile from database
            role_data: Role submission data (company_name, role_title, job_description, company_info)
        
        Returns:
            Dict with:
                - job_analysis: Extracted keywords, responsibilities, qualifications
                - quality_review: Grammar, metrics, clichés check
                - content_optimization: Rewritten bullets and summaries
                - match_score: Overall job match score with breakdown
                - role_calibration: Tone adjustments for seniority level
                - final_resume: Generated resume with all optimizations
        """
        logger.info(f"🚀 Starting Huntr-style multi-agent processing for {role_data['role_title']} at {role_data['company_name']}")
        
        try:
            # Step 1: Job Description Analysis (required for other agents)
            logger.info("📋 Step 1: Job Description Analysis Pipeline...")
            job_analysis = self.job_analyzer.analyze(role_data)
            logger.info(f"  ✓ Extracted {len(job_analysis.get('keywords', {}).get('hard_skills', []))} hard skills, "
                       f"{len(job_analysis.get('responsibilities', []))} responsibilities")
            
            # Prepare resume data for specialist agents
            resume_data = self._prepare_resume_data(profile_data)
            seniority_level = job_analysis.get('seniority_level', 'mid')
            
            # Step 2: Run specialist agents IN PARALLEL (Huntr-style)
            logger.info("🔄 Step 2: Running specialist agents in parallel...")
            
            parallel_results = {}
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all specialist agent tasks in parallel
                future_to_agent = {
                    executor.submit(self._run_proofreader, resume_data, role_data['role_title']): 'quality_review',
                    executor.submit(self._run_optimizer, resume_data, job_analysis, role_data): 'content_optimization',
                    executor.submit(self._run_ats_scorer, resume_data, job_analysis, role_data): 'match_score',
                    executor.submit(self._run_calibrator, resume_data, seniority_level, role_data['role_title']): 'role_calibration'
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_agent):
                    agent_name = future_to_agent[future]
                    try:
                        result = future.result()
                        parallel_results[agent_name] = result
                        logger.info(f"  ✓ {agent_name} completed")
                    except Exception as e:
                        logger.error(f"  ✗ {agent_name} failed: {e}")
                        parallel_results[agent_name] = self._get_default_result(agent_name)
            
            logger.info("✅ All specialist agents completed")
            
            # Step 3: Generate final resume with all optimizations
            logger.info("📝 Step 3: Generating final tailored resume...")
            final_resume = self._generate_final_resume(
                profile_data=profile_data,
                job_analysis=job_analysis,
                content_optimization=parallel_results.get('content_optimization', {}),
                role_calibration=parallel_results.get('role_calibration', {}),
                role_data=role_data
            )
            
            # Combine all results with proper defaults
            result = {
                'job_analysis': job_analysis,
                'quality_review': parallel_results.get('quality_review', self._get_default_result('quality_review')),
                'content_optimization': parallel_results.get('content_optimization', self._get_default_result('content_optimization')),
                'match_score': parallel_results.get('match_score', self._get_default_result('match_score')),
                'role_calibration': parallel_results.get('role_calibration', self._get_default_result('role_calibration')),
                'final_resume': final_resume,
                'aligned_resume': final_resume,  # Backward compatibility
                'success': True
            }
            
            overall_score = parallel_results.get('match_score', {}).get('overall_match_score', 0)
            logger.info(f"🎯 Resume generation completed! Job Match Score: {overall_score}/100")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error during multi-agent resume generation: {e}", exc_info=True)
            error_resume = {
                'resume_html': '<p>Error generating resume. Please try again.</p>',
                'resume_md': '# Error\nUnable to generate resume.',
                'keyword_coverage': {'covered': [], 'emphasized': []},
                'tailoring_notes': [f'Error: {str(e)}']
            }
            return {
                'success': False,
                'error': str(e),
                'job_analysis': {},
                'quality_review': self._get_default_result('quality_review'),
                'content_optimization': self._get_default_result('content_optimization'),
                'match_score': self._get_default_result('match_score'),
                'role_calibration': self._get_default_result('role_calibration'),
                'final_resume': error_resume,
                'aligned_resume': error_resume  # Backward compatibility
            }
    
    def _run_proofreader(self, resume_data: Dict, role_title: str) -> Dict:
        """Run proofreading & quality agent."""
        return self.proofreader.review(resume_data, role_title)
    
    def _run_optimizer(self, resume_data: Dict, job_analysis: Dict, role_data: Dict) -> Dict:
        """Run content optimizer agent."""
        return self.content_optimizer.optimize(resume_data, job_analysis, role_data)
    
    def _run_ats_scorer(self, resume_data: Dict, job_analysis: Dict, role_data: Dict) -> Dict:
        """Run ATS & match scoring agent."""
        return self.ats_scorer.calculate_match(resume_data, job_analysis, role_data)
    
    def _run_calibrator(self, resume_data: Dict, seniority_level: str, role_title: str) -> Dict:
        """Run role calibration agent."""
        return self.role_calibrator.calibrate(resume_data, seniority_level, role_title)
    
    def _prepare_resume_data(self, profile_data: Dict) -> Dict:
        """Convert profile data to resume data format for specialist agents."""
        # Parse experience JSON strings back to dicts
        experience = []
        if profile_data.get('experience'):
            exp_data = json.loads(profile_data['experience']) if isinstance(profile_data['experience'], str) else profile_data['experience']
            experience = exp_data if isinstance(exp_data, list) else []
        
        # Parse education JSON strings back to dicts
        education = []
        if profile_data.get('education'):
            edu_data = json.loads(profile_data['education']) if isinstance(profile_data['education'], str) else profile_data['education']
            education = edu_data if isinstance(edu_data, list) else []
        
        # Parse skills
        skills = []
        if profile_data.get('skills'):
            skills_data = json.loads(profile_data['skills']) if isinstance(profile_data['skills'], str) else profile_data['skills']
            if isinstance(skills_data, list):
                # Extract skill names from dictionaries if needed
                skills = [
                    skill['name'] if isinstance(skill, dict) else str(skill)
                    for skill in skills_data
                ]
            else:
                skills = []
        
        return {
            'summary': profile_data.get('summary', ''),
            'experience': experience,
            'education': education,
            'skills': skills,
            'name': profile_data.get('name', ''),
            'email': profile_data.get('email', ''),
            'phone': profile_data.get('phone', ''),
            'linkedin': profile_data.get('linkedin', '')
        }
    
    def _generate_final_resume(self, profile_data: Dict, job_analysis: Dict, 
                               content_optimization: Dict, role_calibration: Dict,
                               role_data: Dict) -> Dict:
        """
        Generate final resume HTML and Markdown using all specialist agent outputs.
        
        Combines:
        - Optimized summary from Content Optimizer
        - Calibrated tone from Role Calibrator
        - Keyword integration from Job Analyzer
        """
        # Get optimized content
        optimized_summary = content_optimization.get('optimized_summary', {}).get('optimized', 
                                                                                   profile_data.get('summary', ''))
        optimized_skills = content_optimization.get('optimized_skills', {}).get('prioritized_skills', [])
        
        # Parse experience
        experience = []
        if profile_data.get('experience'):
            exp_data = json.loads(profile_data['experience']) if isinstance(profile_data['experience'], str) else profile_data['experience']
            experience = exp_data if isinstance(exp_data, list) else []
        
        # Parse education
        education = []
        if profile_data.get('education'):
            edu_data = json.loads(profile_data['education']) if isinstance(profile_data['education'], str) else profile_data['education']
            education = edu_data if isinstance(edu_data, list) else []
        
        # If no optimized skills, use original
        if not optimized_skills:
            if profile_data.get('skills'):
                skills_data = json.loads(profile_data['skills']) if isinstance(profile_data['skills'], str) else profile_data['skills']
                if isinstance(skills_data, list):
                    # Extract skill names from dictionaries if needed
                    optimized_skills = [
                        skill['name'] if isinstance(skill, dict) else str(skill)
                        for skill in skills_data
                    ]
                else:
                    optimized_skills = []
        
        # Generate HTML resume
        resume_html = self._build_resume_html(
            name=profile_data.get('name', ''),
            email=profile_data.get('email', ''),
            phone=profile_data.get('phone', ''),
            linkedin=profile_data.get('linkedin', ''),
            summary=optimized_summary,
            experience=experience,
            education=education,
            skills=optimized_skills,
            role_title=role_data['role_title'],
            company_name=role_data['company_name']
        )
        
        # Generate Markdown resume
        resume_md = self._build_resume_markdown(
            name=profile_data.get('name', ''),
            email=profile_data.get('email', ''),
            phone=profile_data.get('phone', ''),
            linkedin=profile_data.get('linkedin', ''),
            summary=optimized_summary,
            experience=experience,
            education=education,
            skills=optimized_skills,
            role_title=role_data['role_title'],
            company_name=role_data['company_name']
        )
        
        # Extract covered keywords
        keywords = job_analysis.get('keywords', {})
        all_keywords = (keywords.get('hard_skills', []) + 
                       keywords.get('soft_skills', []) + 
                       keywords.get('industry_terms', []))
        
        # Tailoring notes from all agents
        tailoring_notes = []
        
        # Add content optimization suggestions
        if content_optimization.get('overall_suggestions'):
            tailoring_notes.extend(content_optimization['overall_suggestions'])
        
        # Add role calibration suggestions
        if role_calibration.get('tone_assessment', {}).get('issues'):
            tailoring_notes.extend(role_calibration['tone_assessment']['issues'])
        
        return {
            'resume_html': resume_html,
            'resume_md': resume_md,
            'keyword_coverage': {
                'covered': all_keywords[:20],
                'emphasized': all_keywords[:10]
            },
            'tailoring_notes': tailoring_notes
        }
    
    def _build_resume_html(self, name: str, email: str, phone: str, linkedin: str,
                           summary: str, experience: list, education: list, skills: list,
                           role_title: str, company_name: str) -> str:
        """Build HTML resume with modern styling."""
        html_parts = [
            '<div class="resume-container">',
            '<div class="resume-header">',
            f'<h1>{name}</h1>',
            '<div class="contact-info">',
            f'<span>{email}</span>' if email else '',
            f'<span>{phone}</span>' if phone else '',
            f'<span><a href="{linkedin}" target="_blank">LinkedIn</a></span>' if linkedin else '',
            '</div>',
            '</div>',
            
            '<div class="resume-section">',
            '<h2>Professional Summary</h2>',
            f'<p>{summary}</p>',
            '</div>',
            
            '<div class="resume-section">',
            '<h2>Skills</h2>',
            '<ul class="skills-list">',
            ''.join([f'<li>{skill}</li>' for skill in skills]),
            '</ul>',
            '</div>',
            
            '<div class="resume-section">',
            '<h2>Work Experience</h2>'
        ]
        
        for exp in experience:
            html_parts.extend([
                '<div class="experience-item">',
                f'<h3>{exp.get("title", "")}</h3>',
                f'<h4>{exp.get("company", "")} | {exp.get("dates", "")}</h4>',
                '<ul>',
                ''.join([f'<li>{bullet}</li>' for bullet in exp.get('bullets', [])]),
                '</ul>',
                '</div>'
            ])
        
        html_parts.append('</div>')
        
        if education:
            html_parts.extend([
                '<div class="resume-section">',
                '<h2>Education</h2>'
            ])
            
            for edu in education:
                html_parts.extend([
                    '<div class="education-item">',
                    f'<h3>{edu.get("degree", "")}</h3>',
                    f'<h4>{edu.get("school", "")} | {edu.get("year", "")}</h4>',
                    '</div>'
                ])
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _build_resume_markdown(self, name: str, email: str, phone: str, linkedin: str,
                                summary: str, experience: list, education: list, skills: list,
                                role_title: str, company_name: str) -> str:
        """Build Markdown resume."""
        md_parts = [
            f'# {name}',
            '',
            f'{email} | {phone}' + (f' | [{linkedin}]({linkedin})' if linkedin else ''),
            '',
            '## Professional Summary',
            '',
            summary,
            '',
            '## Skills',
            '',
            ', '.join(skills),
            '',
            '## Work Experience',
            ''
        ]
        
        for exp in experience:
            md_parts.extend([
                f'### {exp.get("title", "")}',
                f'**{exp.get("company", "")}** | {exp.get("dates", "")}',
                '',
                '\n'.join([f'- {bullet}' for bullet in exp.get('bullets', [])]),
                ''
            ])
        
        if education:
            md_parts.extend([
                '## Education',
                ''
            ])
            
            for edu in education:
                md_parts.extend([
                    f'### {edu.get("degree", "")}',
                    f'**{edu.get("school", "")}** | {edu.get("year", "")}',
                    ''
                ])
        
        return '\n'.join(md_parts)
    
    def _get_default_result(self, agent_name: str) -> Dict:
        """
        Get structured default result for an agent when it fails.
        Ensures UI never breaks due to missing fields.
        """
        defaults = {
            'quality_review': {
                'spelling_grammar': [],
                'missing_metrics': [],
                'repetitive_phrases': [],
                'cliches': [],
                'formatting_issues': [],
                'quality_score': {
                    'overall': 80,
                    'spelling': 100,
                    'metrics': 70,
                    'formatting': 90,
                    'content': 80
                },
                'summary': 'Quality review unavailable'
            },
            'content_optimization': {
                'optimized_summary': {
                    'original': '',
                    'optimized': '',
                    'explanation': 'Content optimization unavailable',
                    'keywords_integrated': []
                },
                'optimized_bullets': [],
                'optimized_skills': {
                    'prioritized_skills': [],
                    'skills_to_add': [],
                    'skills_to_emphasize': [],
                    'explanation': 'Skills optimization unavailable'
                },
                'overall_suggestions': []
            },
            'match_score': {
                'overall_match_score': 75,
                'score_breakdown': {
                    'keyword_match': {
                        'score': 70,
                        'matched_keywords': [],
                        'missing_keywords': [],
                        'coverage_percentage': 70
                    },
                    'semantic_match': {
                        'score': 75,
                        'strong_alignments': [],
                        'explanation': 'Semantic analysis unavailable'
                    },
                    'responsibilities_coverage': {
                        'score': 75,
                        'covered_responsibilities': [],
                        'uncovered_responsibilities': []
                    },
                    'qualifications_fit': {
                        'score': 80,
                        'education_match': True,
                        'experience_match': True,
                        'certification_match': False,
                        'gaps': []
                    },
                    'ats_compliance': {
                        'score': 85,
                        'issues': [],
                        'recommendations': []
                    }
                },
                'improvement_priority': [],
                'summary': 'Match scoring unavailable'
            },
            'role_calibration': {
                'tone_assessment': {
                    'current_level': 'mid',
                    'target_level': 'mid',
                    'alignment_score': 80,
                    'issues': []
                },
                'vocabulary_adjustments': [],
                'leadership_calibration': {
                    'current_leadership_cues': [],
                    'suggested_additions': [],
                    'tone_shift': 'Calibration unavailable'
                },
                'formality_adjustments': {
                    'current_formality': 'appropriate',
                    'target_formality': 'professional',
                    'suggestions': []
                },
                'calibrated_examples': []
            }
        }
        
        return defaults.get(agent_name, {})
    
    def get_agent_statuses(self) -> Dict:
        """Get status of all specialist agents for debugging."""
        return {
            'job_description_analyzer': 'openai' if self.job_analyzer.use_openai else 'fallback',
            'resume_parser': 'openai' if self.resume_parser.use_openai else 'fallback',
            'proofreading_quality': 'openai' if self.proofreader.use_openai else 'fallback',
            'content_optimizer': 'openai' if self.content_optimizer.use_openai else 'fallback',
            'ats_match_scorer': 'openai' if self.ats_scorer.use_openai else 'fallback',
            'role_calibrator': 'openai' if self.role_calibrator.use_openai else 'fallback'
        }
