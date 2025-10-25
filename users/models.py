from django.db import models

from django.contrib.auth.models import User


class Account(models.Model):
    EXPERIENCE_LEVELS = (
        ('junior', 'Junior (0-2 years)'),
        ('mid', 'Mid-level (3-5 years)'),
        ('senior', 'Senior (6+ years)'),
    )
    
    AVAILABILITY_STATUS = (
        ('open', 'Open to work'),
        ('busy', 'Busy'),
        ('available', 'Available for projects'),
        ('not_looking', 'Not looking'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='/avatars/default.jpg', upload_to='avatars')
    summary = models.TextField('Summary about user', default='New user on our platform!')
    location = models.TextField('Place of residence', default='Location is not specified.')
    about = models.TextField('About', default='Apparently, this user prefers to keep an air of mystery about them.')
    other_skills = models.TextField('Other skills', null=True, blank=True, help_text='Comma-separated skills')
    
    # New filtering fields
    experience_level = models.CharField(
        'Experience Level', 
        max_length=10, 
        choices=EXPERIENCE_LEVELS, 
        default='junior',
        help_text='Select your experience level'
    )
    availability_status = models.CharField(
        'Availability Status', 
        max_length=15, 
        choices=AVAILABILITY_STATUS, 
        default='available',
        help_text='Your current availability status'
    )
    technology_stack = models.TextField(
        'Technology Stack', 
        null=True, 
        blank=True, 
        help_text='Comma-separated technologies you work with (e.g., Python, React, Django)'
    )
    
    # Resume/Portfolio fields
    resume_file = models.FileField(upload_to='resumes/', null=True, blank=True, help_text='Upload your resume/portfolio as DOCX file')
    resume_content = models.TextField('Resume Content', null=True, blank=True, help_text='Extracted content from resume')
    resume_skills = models.TextField('Resume Skills', null=True, blank=True, help_text='Skills extracted from resume')
    resume_experience = models.TextField('Resume Experience', null=True, blank=True, help_text='Experience extracted from resume')
    resume_education = models.TextField('Resume Education', null=True, blank=True, help_text='Education extracted from resume')

    def __str__(self):
        return f'{self.user.username} Account'


class SkillCategory(models.Model):
    """Categories for organizing skills"""
    name = models.CharField('Category Name', max_length=50, unique=True)
    description = models.TextField('Description', blank=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Skill Categories'


class Skill(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField('Skill name', max_length=50)
    description = models.TextField('Skill description')
    category = models.ForeignKey(SkillCategory, on_delete=models.SET_NULL, null=True, blank=True)
    proficiency_level = models.IntegerField(
        'Proficiency Level', 
        default=1, 
        help_text='Skill level from 1 (Beginner) to 5 (Expert)'
    )

    def __str__(self):
        return f'{self.account} - {self.name} Skill'

    class Meta:
        ordering = ['-proficiency_level', 'name']


class Link(models.Model):
    ICONS = (
        ('im im-github', 'GitHub'),
        ('im im-stackoverflow', 'StackOverflow'),
        ('im im-linkedin', 'LinkedIn'),
        ('im im-twitter', 'Twitter'),
        ('im im-globe', 'Website')
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField('Link name', max_length=30)
    link = models.URLField('URL')
    icon = models.TextField('Icon name', choices=ICONS)

    def __str__(self):
        return f'{self.name} Link'
