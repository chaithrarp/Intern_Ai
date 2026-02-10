from typing import List, Dict
import random

class ResumeQuestionGenerator:
    """Generates interview questions based on resume content"""
    
    def __init__(self):
        self.question_templates = {
            "experience": [
                "I see you worked at {company}. Can you tell me about your role there?",
                "What were your main responsibilities at {company}?",
                "Can you describe a challenging project you worked on at {company}?",
            ],
            "skills": [
                "I notice you have experience with {skill}. How have you applied this in your work?",
                "Can you give me an example of how you've used {skill} in a project?",
                "How would you rate your proficiency in {skill} and why?",
            ],
            "education": [
                "I see you studied {field}. How has this prepared you for this role?",
                "What was your favorite course during your {degree} and why?",
            ],
            "projects": [
                "Can you walk me through the {project} project mentioned in your resume?",
                "What was your specific contribution to {project}?",
                "What challenges did you face during {project} and how did you overcome them?",
            ],
            "general": [
                "Based on your background, why are you interested in this position?",
                "How do your experiences align with what we're looking for?",
                "What do you think makes you a strong candidate for this role?",
            ]
        }
    
    def extract_keywords(self, resume_text: str) -> Dict[str, List[str]]:
        """Extract potential keywords from resume for question generation"""
        keywords = {
            "companies": [],
            "skills": [],
            "projects": [],
            "technologies": []
        }
        
        # Simple keyword extraction (you can enhance this with NLP)
        lines = resume_text.split('\n')
        
        # Common tech skills to look for
        tech_keywords = ['python', 'java', 'javascript', 'react', 'node', 'sql', 
                        'machine learning', 'ai', 'data analysis', 'aws', 'docker',
                        'kubernetes', 'git', 'agile', 'scrum']
        
        text_lower = resume_text.lower()
        for skill in tech_keywords:
            if skill in text_lower:
                keywords["skills"].append(skill)
        
        return keywords
    
    def generate_questions(self, resume_text: str, num_questions: int = 5) -> List[str]:
        """Generate interview questions based on resume content"""
        questions = []
        keywords = self.extract_keywords(resume_text)
        
        # Add general resume-based questions
        questions.extend(self.question_templates["general"])
        
        # Add skill-based questions
        for skill in keywords["skills"][:2]:
            template = random.choice(self.question_templates["skills"])
            questions.append(template.replace("{skill}", skill))
        
        # Add more general questions if needed
        default_questions = [
            "Can you walk me through your resume and highlight your most relevant experiences?",
            "What achievement from your resume are you most proud of?",
            "I see several interesting experiences on your resume. Which one taught you the most?",
            "How have your past experiences prepared you for this role?",
        ]
        
        questions.extend(default_questions)
        
        return questions[:num_questions]
    
    def create_resume_context(self, resume_text: str) -> str:
        """Create a context string for the LLM about the candidate's resume"""
        
        # Extract key information for better context
        keywords = self.extract_keywords(resume_text)
        
        # Summarize key points
        skills_mentioned = ", ".join(keywords["skills"][:5]) if keywords["skills"] else "various technologies"
        
        context = f"""CANDIDATE'S RESUME SUMMARY:
    =====================================

    {resume_text[:1500]}... 

    KEY SKILLS IDENTIFIED: {skills_mentioned}

    =====================================

    INTERVIEW INSTRUCTIONS:
    - You are conducting a PERSONALIZED interview based on the candidate's actual resume above
    - Ask questions that reference SPECIFIC details from their resume (companies, projects, technologies)
    - Make the interview feel realistic by mentioning things you "noticed" on their resume
    - Start with their background, then dive deeper into specific experiences
    - Ask follow-up questions based on what they mention from their resume

    EXAMPLE GOOD QUESTIONS:
    - "I see you worked with {skills_mentioned}. Can you tell me about a specific project where you used these?"
    - "I noticed you worked at [mention a company from resume if visible]. What was your role there?"
    - "Walk me through your background and highlight the experiences most relevant to this role."

    DO NOT ask generic questions - make it personal to THEIR resume!"""
        
        return context