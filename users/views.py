from django.shortcuts import render, redirect
from django.contrib import messages

from django.contrib.auth.models import User

from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.db import IntegrityError
from django.http import HttpResponseForbidden
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .models import Skill
from main.models import Project

import os
import re
import tempfile
from docx import Document
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


def extract_text_from_pdf(pdf_file):
    """
    Extract text from PDF file using both direct text extraction and OCR
    """
    try:
        # First try direct text extraction
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        # If direct extraction didn't work well, try OCR
        if len(text.strip()) < 100:  # If very little text was extracted
            # Convert PDF to images and use OCR
            pdf_file.seek(0)  # Reset file pointer
            images = convert_from_path(pdf_file.name)
            
            ocr_text = ""
            for image in images:
                ocr_text += pytesseract.image_to_string(image) + "\n"
            
            if len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
        
        return text
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"


def extract_text_from_docx(docx_file):
    """
    Extract text from DOCX file
    """
    try:
        doc = Document(docx_file)
        full_text = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                full_text.append(paragraph.text.strip())
        
        return '\n'.join(full_text)
    except Exception as e:
        return f"Error extracting DOCX text: {str(e)}"


def extract_resume_content(file, file_type):
    """
    Extract content from resume file (DOCX or PDF) and categorize it
    """
    try:
        # Extract text based on file type
        if file_type == 'pdf':
            content = extract_text_from_pdf(file)
        else:  # docx
            content = extract_text_from_docx(file)
        
        # Enhanced skill keywords with more comprehensive list
        skill_keywords = [
            # Programming Languages
            'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin',
            'typescript', 'scala', 'r', 'matlab', 'perl', 'haskell', 'clojure', 'erlang',
            
            # Web Frameworks
            'react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel', 'express', 'fastapi',
            'rails', 'asp.net', 'symfony', 'codeigniter', 'cakephp', 'yii', 'zend',
            
            # Databases
            'sql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'cassandra',
            'oracle', 'sqlite', 'mariadb', 'neo4j', 'dynamodb', 'couchdb',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github',
            'terraform', 'ansible', 'chef', 'puppet', 'vagrant', 'consul', 'vault',
            
            # Frontend Technologies
            'html', 'css', 'bootstrap', 'tailwind', 'sass', 'scss', 'less', 'webpack',
            'gulp', 'grunt', 'npm', 'yarn', 'babel', 'eslint', 'prettier',
            
            # Mobile Development
            'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic', 'cordova',
            
            # Data Science & AI
            'machine learning', 'ai', 'artificial intelligence', 'data science', 'analytics',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'matplotlib',
            'seaborn', 'plotly', 'jupyter', 'spark', 'hadoop', 'kafka',
            
            # Methodologies
            'agile', 'scrum', 'kanban', 'devops', 'ci/cd', 'testing', 'tdd', 'bdd',
            'microservices', 'api', 'rest', 'graphql', 'soap', 'webhook',
            
            # Tools & Platforms
            'git', 'svn', 'mercurial', 'jira', 'confluence', 'slack', 'teams',
            'postman', 'insomnia', 'swagger', 'docker compose', 'kubernetes',
            
            # Operating Systems
            'linux', 'unix', 'windows', 'macos', 'ubuntu', 'centos', 'debian',
            
            # Other Technologies
            'blockchain', 'ethereum', 'solidity', 'web3', 'nft', 'cryptocurrency',
            'iot', 'arduino', 'raspberry pi', 'mqtt', 'coap'
        ]
        
        # Extract skills
        found_skills = []
        content_lower = content.lower()
        for skill in skill_keywords:
            if skill in content_lower:
                found_skills.append(skill.title())
        
        # Extract projects (look for project descriptions, portfolio items)
        project_patterns = [
            r'(?:project|portfolio|application|website|app|system|platform|tool|software|dashboard|e-commerce|mobile|web).*?(?:built|developed|created|designed|implemented)',
            r'(?:built|developed|created|designed|implemented).*?(?:project|application|website|app|system|platform|tool|software|dashboard|e-commerce|mobile|web)',
            r'(?:github|gitlab|bitbucket).*?/([a-zA-Z0-9\-_]+)',
            r'(?:www\.|https?://)([a-zA-Z0-9\-_]+\.(?:com|org|net|io|co|dev))',
            r'(?:E-Commerce|Machine Learning|Mobile|Web|Dashboard|API|REST|Full-stack|Cross-platform).*?(?:Platform|Application|System|Tool|Dashboard|API)',
            r'(?:React|Django|Flask|Node\.js|Angular|Vue).*?(?:application|project|website|app|system)',
        ]
        
        projects = []
        for pattern in project_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            projects.extend(matches)
        
        # Extract experience
        experience_patterns = [
            r'(?:worked|experience|employed|position|role).*?(?:at|in|for)\s+([A-Z][a-zA-Z\s&\.]+)',
            r'(?:software engineer|developer|programmer|analyst|manager|director|lead|senior|junior|intern).*?(?:at|in|for)\s+([A-Z][a-zA-Z\s&\.]+)',
            r'([A-Z][a-zA-Z\s&\.]+)\s+(?:software engineer|developer|programmer|analyst|manager|director|lead)',
        ]
        
        experience = []
        for pattern in experience_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            experience.extend(matches)
        
        # Extract education
        education_patterns = [
            r'(?:bachelor|master|phd|degree|diploma|certificate).*?(?:in|of)\s+([A-Z][a-zA-Z\s&\.]+)',
            r'(?:university|college|institute|school).*?([A-Z][a-zA-Z\s&\.]+)',
            r'([A-Z][a-zA-Z\s&\.]+)\s+(?:university|college|institute)',
        ]
        
        education = []
        for pattern in education_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            education.extend(matches)
        
        return {
            'content': content,
            'skills': ', '.join(list(set(found_skills))),
            'projects': ', '.join(list(set(projects))),
            'experience': ', '.join(list(set(experience))),
            'education': ', '.join(list(set(education)))
        }
    except Exception as e:
        return {
            'content': f'Error processing file: {str(e)}',
            'skills': '',
            'projects': '',
            'experience': '',
            'education': ''
        }


def auto_populate_skills_and_projects(user_account, extracted_data):
    """
    Automatically populate user's skills and projects based on extracted resume data
    """
    try:
        # Auto-populate skills
        if extracted_data.get('skills'):
            skills_list = [skill.strip() for skill in extracted_data['skills'].split(',') if skill.strip()]
            
            # Clear existing skills first
            user_account.skill_set.all().delete()
            
            # Add new skills
            for skill_name in skills_list[:10]:  # Limit to 10 skills
                if len(skill_name) <= 50:  # Reasonable skill name length
                    skill = Skill(
                        account=user_account,
                        name=skill_name,
                        description=f"Extracted from resume - {skill_name} skill"
                    )
                    skill.save()
        
        # Auto-populate projects
        if extracted_data.get('projects'):
            projects_list = [project.strip() for project in extracted_data['projects'].split(',') if project.strip()]
            
            # Clear existing projects first
            Project.objects.filter(user=user_account.user).delete()
            
            # Add new projects
            for i, project_name in enumerate(projects_list[:5]):  # Limit to 5 projects
                if len(project_name) <= 100:  # Reasonable project name length
                    # Get first 3 skills for tags
                    skills_for_tags = [skill.strip() for skill in extracted_data.get('skills', '').split(',')[:3] if skill.strip()]
                    tags_string = ', '.join(skills_for_tags) if skills_for_tags else 'Resume Project'
                    
                    project = Project(
                        user=user_account.user,
                        title=project_name,
                        description=f"Project extracted from resume - {project_name}",
                        tags=tags_string,
                        link="https://example.com",  # Default link since it's required
                        image=None  # No image available
                    )
                    project.save()
        
        return True
    except Exception as e:
        print(f"Error auto-populating skills and projects: {e}")
        return False


def signup(request):
    if request.method == 'POST':
        if ' ' not in request.POST.get('name'):
            messages.info(request, 'Full name is incorrect!')
        elif request.POST.get('password') != request.POST.get('confirm-password'):
            messages.info(request, 'Passwords do not match!')

        else:
            user = User(
                first_name=request.POST.get('name').rsplit(' ')[0],
                last_name=request.POST.get('name').rsplit(' ')[1],
                username=request.POST.get('email'),
                email=request.POST.get('email'),
                password=make_password(request.POST.get('password'))
            )
            try:
                user.save()
                return redirect('login')
            except IntegrityError:
                messages.info(request, 'This user is already exist!')

    return render(request, 'signup.html')


def signin(request):
    if request.method == 'POST':
        user = authenticate(
            username=request.POST.get('email'),
            password=request.POST.get('password')
        )
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.info(request, 'Email or password is incorrect!')

    return render(request, 'login.html')


def logOut(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def account(request):
    context = {
        'user': request.user,
        'projects': Project.objects.filter(user=request.user).order_by('-date')
    }
    return render(request, 'account.html', context)


def profile(request, username):
    user = User.objects.get(username=username)
    context = {
        'user': user,
        'projects': Project.objects.filter(user=user).order_by('-date')
    }
    return render(request, 'profile.html', context)


# ACCOUNT STUFF
@login_required(login_url='login')
def editAccount(request):
    user = request.user
    if request.method == 'POST':
        if ' ' not in request.POST.get('full_name'):
            messages.info(request, 'Full name is incorrect!')

        else:
            user.first_name = request.POST.get('full_name').rsplit(' ')[0]
            user.last_name = request.POST.get('full_name').rsplit(' ')[1]
            user.email = request.POST.get('email')
            user.account.summary = request.POST.get('summary')
            user.account.location = request.POST.get('location')
            user.account.about = request.POST.get('about')
            user.account.other_skills = request.POST.get('skills').rsplit(', ')
            if request.FILES.get('avatar') is not None:
                user.account.avatar = request.FILES.get('avatar')

            user.save()
            return redirect('account')

    return render(request, 'account-edit-form.html', {'user': user})


@login_required(login_url='login')
def addSkill(request):
    if request.method == 'POST':
        skill = Skill(
            account=request.user.account,
            name=request.POST.get('name'),
            description=request.POST.get('desc')
        )
        skill.save()
        return redirect('account')

    return render(request, 'skill-add-edit-form.html')


@login_required(login_url='login')
def editSkill(request, id):
    skill = Skill.objects.get(id=id)
    if skill.account.user == request.user:
        if request.method == 'POST':
            skill.name = request.POST.get('name')
            skill.description = request.POST.get('desc')
            skill.save()
            return redirect('account')
        else:
            return render(request, 'skill-add-edit-form.html', {'skill': skill})
    else:
        return HttpResponseForbidden()


@login_required(login_url='login')
def deleteSkill(request, id):
    skill = Skill.objects.get(id=id)
    if skill.account.user == request.user:
        if request.method == 'POST':
            skill.delete()
            return redirect('account')
        else:
            context = {
                'warning': f'Are your sure you want to delete this {skill.name} skill?'
            }
            return render(request, 'delete.html', context)
    else:
        return HttpResponseForbidden()


@login_required(login_url='login')
def addProject(request):
    if request.method == 'POST':
        project = Project(
            user=request.user,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            tags=request.POST.get('tags').rsplit(', '),
            link=request.POST.get('link'),
            image=request.FILES.get('image')
        )
        project.save()
        return redirect('account')

    return render(request, 'project-add-edit-form.html')


@login_required(login_url='login')
def editProject(request, id):
    project = Project.objects.get(id=id)
    if project.user == request.user:
        if request.method == 'POST':
            project.title = request.POST.get('title')
            project.description = request.POST.get('description')
            project.link = request.POST.get('link')
            project.tags = request.POST.get('tags').rsplit(', ')
            if request.FILES.get('image'):
                project.image = request.FILES.get('image')

            project.save()
            return redirect('account')

        return render(request, 'project-add-edit-form.html', {'project': project})

    else:
        return HttpResponseForbidden()


@login_required(login_url='login')
def deleteProject(request, id):
    project = Project.objects.get(id=id)
    if project.user == request.user:
        if request.method == 'POST':
            project.delete()
            return redirect('account')

        context = {
            'warning': f'Are your sure you want to delete this {project.title} project?'
        }
        return render(request, 'delete.html', context)

    else:
        return HttpResponseForbidden()


@login_required(login_url='login')
def uploadResume(request):
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        
        if resume_file:
            # Check if file is DOCX or PDF
            file_extension = resume_file.name.lower().split('.')[-1]
            if file_extension not in ['docx', 'pdf']:
                messages.error(request, 'Please upload a DOCX or PDF file.')
                return redirect('account')
            
            # Save the file
            user_account = request.user.account
            user_account.resume_file = resume_file
            
            # Extract content based on file type
            extracted_data = extract_resume_content(resume_file, file_extension)
            
            # Save extracted data
            user_account.resume_content = extracted_data['content']
            user_account.resume_skills = extracted_data['skills']
            user_account.resume_experience = extracted_data['experience']
            user_account.resume_education = extracted_data['education']
            
            user_account.save()
            
            # Auto-populate skills and projects
            auto_populate_skills_and_projects(user_account, extracted_data)
            
            messages.success(request, f'Resume uploaded and processed successfully! Skills and projects have been automatically updated.')
            return redirect('account')
        else:
            messages.error(request, 'Please select a file to upload.')
    
    return redirect('account')
