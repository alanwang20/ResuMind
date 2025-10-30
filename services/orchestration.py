import logging
import json
from typing import Dict
from services.agents.company_insight_agent import CompanyInsightAgent
from services.agents.experience_summarizer_agent import ExperienceSummarizerAgent
from services.agents.alignment_agent import AlignmentAgent

logger = logging.getLogger(__name__)


class ResumeOrchestrator:
    """
    Orchestrates the multi-agent resume generation workflow.
    Coordinates Company Insight, Experience Summarizer, and Alignment agents.
    """
    
    def __init__(self, use_openai: bool = True):
        self.use_openai = use_openai
        self.company_insight_agent = CompanyInsightAgent(use_openai)
        self.experience_summarizer_agent = ExperienceSummarizerAgent(use_openai)
        self.alignment_agent = AlignmentAgent(use_openai)
        logger.info(f"ResumeOrchestrator initialized (OpenAI: {use_openai})")
    
    def generate_tailored_resume(self, profile_data: Dict, role_data: Dict) -> Dict:
        """
        Main orchestration method that runs all three agents in sequence.
        
        Args:
            profile_data: Complete user profile from database
            role_data: Role submission data (company_name, role_title, job_description, company_info)
        
        Returns:
            Dict with:
                - company_insights: Output from Company Insight Agent
                - experience_summaries: Output from Experience Summarizer Agent
                - aligned_resume: Output from Alignment Agent (contains resume_html, resume_md, etc.)
        """
        logger.info(f"Starting multi-agent resume generation for {role_data['role_title']} at {role_data['company_name']}")
        
        try:
            logger.info("Step 1/3: Analyzing company and role...")
            company_insights = self.company_insight_agent.analyze(role_data)
            logger.info(f"  ✓ Company insights extracted: {len(company_insights.get('important_keywords', []))} keywords")
            
            logger.info("Step 2/3: Summarizing user profile...")
            experience_summaries = self.experience_summarizer_agent.summarize(profile_data)
            logger.info(f"  ✓ Profile summarized: {len(experience_summaries.get('experience_summaries', []))} experiences")
            
            logger.info("Step 3/3: Aligning experiences with role...")
            aligned_resume = self.alignment_agent.align(
                company_insights=company_insights,
                experience_summaries=experience_summaries,
                role_data=role_data,
                profile_data=profile_data
            )
            logger.info(f"  ✓ Resume aligned: {len(aligned_resume.get('keyword_coverage', {}).get('covered', []))} keywords covered")
            
            result = {
                'company_insights': company_insights,
                'experience_summaries': experience_summaries,
                'aligned_resume': aligned_resume,
                'success': True
            }
            
            logger.info("Multi-agent resume generation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error during multi-agent resume generation: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'company_insights': {},
                'experience_summaries': {},
                'aligned_resume': {
                    'resume_html': '<p>Error generating resume. Please try again.</p>',
                    'resume_md': '# Error\nUnable to generate resume.',
                    'keyword_coverage': {'covered': [], 'emphasized': []},
                    'tailoring_notes': [f'Error: {str(e)}']
                }
            }
    
    def get_agent_statuses(self) -> Dict:
        """Get status of all agents for debugging."""
        return {
            'company_insight_agent': 'openai' if self.company_insight_agent.use_openai else 'fallback',
            'experience_summarizer_agent': 'openai' if self.experience_summarizer_agent.use_openai else 'fallback',
            'alignment_agent': 'openai' if self.alignment_agent.use_openai else 'fallback'
        }
