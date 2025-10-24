from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from .models import Project, Message
from users.models import Account, Skill, SkillCategory


def index(request):
    # Get all filter parameters
    search_query = request.GET.get('search', '')
    location_filter = request.GET.get('location', '')
    experience_filter = request.GET.get('experience', '')
    tech_stack_filter = request.GET.get('tech_stack', '')
    availability_filter = request.GET.get('availability', '')
    skill_filter = request.GET.get('skills', '')
    search_operator = request.GET.get('operator', 'AND')  # AND, OR, NOT
    
    # Start with all users
    users = User.objects.select_related('account').prefetch_related('account__skill_set')
    
    # Build query conditions
    conditions = Q()
    
    # Basic name search
    if search_query:
        name_conditions = Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query) | Q(username__icontains=search_query)
        conditions &= name_conditions
    
    # Location filtering
    if location_filter:
        conditions &= Q(account__location__icontains=location_filter)
    
    # Experience level filtering
    if experience_filter:
        conditions &= Q(account__experience_level=experience_filter)
    
    # Technology stack filtering
    if tech_stack_filter:
        tech_conditions = Q(account__technology_stack__icontains=tech_stack_filter)
        conditions &= tech_conditions
    
    # Availability status filtering
    if availability_filter:
        conditions &= Q(account__availability_status=availability_filter)
    
    # Skill-based filtering with advanced operators
    if skill_filter:
        skills = [skill.strip() for skill in skill_filter.split(',') if skill.strip()]
        if skills:
            skill_conditions = Q()
            for skill in skills:
                skill_query = Q(account__skill_set__name__icontains=skill) | Q(account__other_skills__icontains=skill)
                
                if search_operator == 'OR':
                    skill_conditions |= skill_query
                elif search_operator == 'NOT':
                    skill_conditions &= ~skill_query
                else:  # AND (default)
                    skill_conditions &= skill_query
            
            conditions &= skill_conditions
    
    # Apply all conditions
    if conditions:
        users = users.filter(conditions).distinct()
    
    # Order by date joined
    users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 6)
    page = request.GET.get('page', 1)
    page_users = paginator.get_page(page)
    
    # Get filter options for the template
    all_locations = Account.objects.exclude(location__isnull=True).exclude(location='').values_list('location', flat=True).distinct()
    all_skills = Skill.objects.values_list('name', flat=True).distinct()
    all_tech_stacks = Account.objects.exclude(technology_stack__isnull=True).exclude(technology_stack='').values_list('technology_stack', flat=True).distinct()
    
    context = {
        'users': page_users,
        'search_query': search_query,
        'location_filter': location_filter,
        'experience_filter': experience_filter,
        'tech_stack_filter': tech_stack_filter,
        'availability_filter': availability_filter,
        'skill_filter': skill_filter,
        'search_operator': search_operator,
        'all_locations': all_locations,
        'all_skills': all_skills,
        'all_tech_stacks': all_tech_stacks,
        'experience_levels': Account.EXPERIENCE_LEVELS,
        'availability_statuses': Account.AVAILABILITY_STATUS,
    }
    
    return render(request, 'index.html', context)


def projects(request):
    if request.method == 'POST':
        search_data = request.POST.get('search')
        projects = Project.objects.filter(title__contains=search_data).order_by('-date')
    else:
        projects = Project.objects.order_by('-date')

    paginator = Paginator(projects, 6)
    page = request.GET.get('page', 1)
    page_projects = paginator.get_page(page)

    return render(request, 'projects.html', {'projects': page_projects})


def singleProject(request, id):
    project = Project.objects.get(id=id)
    if request.method == 'POST':
        project.comment_set.create(
            author=request.user,
            text=request.POST.get('message')
        )
        return redirect('single-project', project.id)

    return render(request, 'single-project.html', {'project': project})


@login_required(login_url='login')
def inbox(request):
    messages = Message.objects.filter(user_to=request.user).order_by('-date')
    unread = messages.filter(is_read=False).count()
    return render(request, 'inbox.html', {'messages': messages, 'unread': unread})


@login_required(login_url='login')
def singleMessage(request, id):
    message = Message.objects.get(id=id)
    if message.user_to == request.user:
        message.is_read = True
        message.save()
        return render(request, 'message.html', {'message': message})

    return HttpResponseForbidden


@login_required(login_url='login')
def sendMessage(request, user_id):
    user_to = User.objects.get(id=user_id)
    if request.method == 'POST':
        message = Message(
            user_to=user_to,
            user_from=request.user,
            subject=request.POST.get('subject'),
            text=request.POST.get('text')
        )
        message.save()
        return redirect('profile', user_to.username)

    return render(request, 'send-message.html', {'user_to': user_to})


# API endpoints for autocomplete
@csrf_exempt
@require_http_methods(["GET"])
def skill_autocomplete(request):
    """API endpoint for skill autocomplete"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'skills': []})
    
    skills = Skill.objects.filter(name__icontains=query).values_list('name', flat=True).distinct()[:10]
    return JsonResponse({'skills': list(skills)})


@csrf_exempt
@require_http_methods(["GET"])
def location_autocomplete(request):
    """API endpoint for location autocomplete"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'locations': []})
    
    locations = Account.objects.filter(location__icontains=query).values_list('location', flat=True).distinct()[:10]
    return JsonResponse({'locations': list(locations)})


@csrf_exempt
@require_http_methods(["GET"])
def tech_stack_autocomplete(request):
    """API endpoint for technology stack autocomplete"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'tech_stacks': []})
    
    # Get all technology stacks and split them
    all_tech_stacks = Account.objects.exclude(technology_stack__isnull=True).exclude(technology_stack='').values_list('technology_stack', flat=True)
    tech_list = []
    for stack in all_tech_stacks:
        if stack:
            tech_list.extend([tech.strip() for tech in stack.split(',')])
    
    # Filter and return unique matches
    matching_techs = [tech for tech in set(tech_list) if query.lower() in tech.lower()][:10]
    return JsonResponse({'tech_stacks': matching_techs})
