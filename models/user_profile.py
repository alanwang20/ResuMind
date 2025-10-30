from datetime import datetime
from models import db


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    location = db.Column(db.String(200))
    linkedin = db.Column(db.String(300))
    website = db.Column(db.String(300))
    
    summary = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    education = db.relationship('Education', back_populates='profile', cascade='all, delete-orphan')
    experiences = db.relationship('Experience', back_populates='profile', cascade='all, delete-orphan')
    skills = db.relationship('Skill', back_populates='profile', cascade='all, delete-orphan')
    projects = db.relationship('Project', back_populates='profile', cascade='all, delete-orphan')
    role_submissions = db.relationship('RoleSubmission', back_populates='profile', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
            'linkedin': self.linkedin,
            'website': self.website,
            'summary': self.summary,
            'education': [edu.to_dict() for edu in self.education],
            'experience': [exp.to_dict() for exp in self.experiences],
            'skills': [skill.to_dict() for skill in self.skills],
            'projects': [proj.to_dict() for proj in self.projects]
        }


class Education(db.Model):
    __tablename__ = 'education'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    
    degree = db.Column(db.String(200), nullable=False)
    field_of_study = db.Column(db.String(200))
    institution = db.Column(db.String(300), nullable=False)
    location = db.Column(db.String(200))
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    gpa = db.Column(db.String(20))
    achievements = db.Column(db.Text)
    
    profile = db.relationship('UserProfile', back_populates='education')
    
    def to_dict(self):
        # Format dates for display
        year = ''
        if self.start_date and self.end_date:
            year = f"{self.start_date} - {self.end_date}"
        elif self.start_date:
            year = self.start_date
        elif self.end_date:
            year = self.end_date
            
        return {
            'id': self.id,
            'degree': self.degree,
            'field_of_study': self.field_of_study,
            'school': self.institution,  # Map to expected field name
            'institution': self.institution,
            'location': self.location,
            'year': year,  # Combined date display
            'start_date': self.start_date,
            'end_date': self.end_date,
            'gpa': self.gpa,
            'achievements': self.achievements
        }


class Experience(db.Model):
    __tablename__ = 'experiences'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(300), nullable=False)
    location = db.Column(db.String(200))
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    achievements = db.Column(db.Text)
    
    profile = db.relationship('UserProfile', back_populates='experiences')
    
    def to_dict(self):
        # Format dates for display
        dates = ''
        if self.current:
            dates = f"{self.start_date} - Present" if self.start_date else "Present"
        elif self.start_date and self.end_date:
            dates = f"{self.start_date} - {self.end_date}"
        elif self.start_date:
            dates = self.start_date
        elif self.end_date:
            dates = self.end_date
        
        # Combine description and achievements into bullets
        bullets = []
        if self.description:
            # Split by newlines or bullet points
            desc_bullets = [line.strip() for line in self.description.split('\n') if line.strip()]
            bullets.extend(desc_bullets)
        if self.achievements:
            ach_bullets = [line.strip() for line in self.achievements.split('\n') if line.strip()]
            bullets.extend(ach_bullets)
            
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'dates': dates,  # Combined date display
            'start_date': self.start_date,
            'end_date': self.end_date,
            'current': self.current,
            'description': self.description,
            'achievements': self.achievements,
            'bullets': bullets  # Formatted bullet points
        }


class Skill(db.Model):
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    
    category = db.Column(db.String(100))
    name = db.Column(db.String(200), nullable=False)
    proficiency = db.Column(db.String(50))
    
    profile = db.relationship('UserProfile', back_populates='skills')
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'name': self.name,
            'proficiency': self.proficiency
        }


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    technologies = db.Column(db.Text)
    url = db.Column(db.String(300))
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    achievements = db.Column(db.Text)
    
    profile = db.relationship('UserProfile', back_populates='projects')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'technologies': self.technologies,
            'url': self.url,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'achievements': self.achievements
        }


class RoleSubmission(db.Model):
    __tablename__ = 'role_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    
    company_name = db.Column(db.String(300), nullable=False)
    role_title = db.Column(db.String(300), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    company_info = db.Column(db.Text)
    
    company_insights = db.Column(db.Text)
    experience_summaries = db.Column(db.Text)
    aligned_resume = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    profile = db.relationship('UserProfile', back_populates='role_submissions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'role_title': self.role_title,
            'job_description': self.job_description,
            'company_info': self.company_info,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
