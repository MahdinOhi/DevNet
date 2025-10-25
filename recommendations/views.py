from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
import json

from .models import RecommendationEngine, UserSimilarity, ProjectSimilarity
from main.models import Project


@require_http_methods(["GET"])
def get_related_users(request, user_id):
    """API endpoint to get related users for a specific user"""
    try:
        user = get_object_or_404(User, id=user_id)
        limit = int(request.GET.get('limit', 5))
        
        related_users = RecommendationEngine.get_related_users(user, limit)
        
        users_data = []
        for related_user, similarity_score in related_users:
            users_data.append({
                'id': related_user.id,
                'username': related_user.username,
                'first_name': related_user.first_name,
                'last_name': related_user.last_name,
                'avatar_url': related_user.account.avatar.url if related_user.account.avatar else None,
                'summary': related_user.account.summary,
                'location': related_user.account.location,
                'experience_level': related_user.account.get_experience_level_display(),
                'availability_status': related_user.account.get_availability_status_display(),
                'similarity_score': round(similarity_score, 3),
                'profile_url': f'/profile/{related_user.username}/'
            })
        
        return JsonResponse({
            'related_users': users_data,
            'total_count': len(users_data)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_related_projects(request, project_id):
    """API endpoint to get related projects for a specific project"""
    try:
        project = get_object_or_404(Project, id=project_id)
        limit = int(request.GET.get('limit', 5))
        
        related_projects = RecommendationEngine.get_related_projects(project, limit)
        
        projects_data = []
        for related_project, similarity_score in related_projects:
            projects_data.append({
                'id': related_project.id,
                'title': related_project.title,
                'description': related_project.description[:200] + '...' if len(related_project.description) > 200 else related_project.description,
                'tags': related_project.tags,
                'link': related_project.link,
                'image_url': related_project.image.url if related_project.image else None,
                'author_name': f"{related_project.user.first_name} {related_project.user.last_name}",
                'author_username': related_project.user.username,
                'author_avatar': related_project.user.account.avatar.url if related_project.user.account.avatar else None,
                'similarity_score': round(similarity_score, 3),
                'project_url': f'/projects/{related_project.id}/',
                'author_profile_url': f'/profile/{related_project.user.username}/'
            })
        
        return JsonResponse({
            'related_projects': projects_data,
            'total_count': len(projects_data)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_user_recommendations(request, user_id):
    """Get comprehensive recommendations for a user (users + projects)"""
    try:
        user = get_object_or_404(User, id=user_id)
        user_limit = int(request.GET.get('user_limit', 3))
        project_limit = int(request.GET.get('project_limit', 3))
        
        # Get related users
        related_users = RecommendationEngine.get_related_users(user, user_limit)
        users_data = []
        for related_user, similarity_score in related_users:
            users_data.append({
                'id': related_user.id,
                'username': related_user.username,
                'first_name': related_user.first_name,
                'last_name': related_user.last_name,
                'avatar_url': related_user.account.avatar.url if related_user.account.avatar else None,
                'summary': related_user.account.summary,
                'similarity_score': round(similarity_score, 3),
                'profile_url': f'/profile/{related_user.username}/'
            })
        
        # Get related projects based on user's skills and interests
        user_projects = user.project_set.all()
        related_projects = []
        
        if user_projects.exists():
            # Get projects similar to user's own projects
            for user_project in user_projects[:2]:  # Check similarity with user's recent projects
                project_similarities = RecommendationEngine.get_related_projects(user_project, project_limit)
                for project, score in project_similarities:
                    if project.user != user:  # Don't recommend user's own projects
                        related_projects.append((project, score))
        
        # If no project-based recommendations, get projects from similar users
        if not related_projects:
            for related_user, _ in related_users[:2]:
                user_projects = related_user.project_set.all()[:project_limit]
                for project in user_projects:
                    related_projects.append((project, 0.5))  # Default similarity for user-based recommendations
        
        # Remove duplicates and sort by similarity
        unique_projects = {}
        for project, score in related_projects:
            if project.id not in unique_projects or unique_projects[project.id][1] < score:
                unique_projects[project.id] = (project, score)
        
        projects_data = []
        for project, similarity_score in sorted(unique_projects.values(), key=lambda x: x[1], reverse=True)[:project_limit]:
            projects_data.append({
                'id': project.id,
                'title': project.title,
                'description': project.description[:150] + '...' if len(project.description) > 150 else project.description,
                'tags': project.tags,
                'image_url': project.image.url if project.image else None,
                'author_name': f"{project.user.first_name} {project.user.last_name}",
                'similarity_score': round(similarity_score, 3),
                'project_url': f'/projects/{project.id}/'
            })
        
        return JsonResponse({
            'related_users': users_data,
            'related_projects': projects_data,
            'user_count': len(users_data),
            'project_count': len(projects_data)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def update_similarities(request):
    """Update all similarities (admin endpoint)"""
    try:
        # This should be protected in production
        RecommendationEngine.update_similarities()
        return JsonResponse({'message': 'Similarities updated successfully'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_similarity_graph(request, user_id):
    """Get similarity graph data for visualization"""
    try:
        user = get_object_or_404(User, id=user_id)
        limit = int(request.GET.get('limit', 10))
        
        # Get user's similarities
        similarities = UserSimilarity.objects.filter(
            user1=user
        ).order_by('-similarity_score')[:limit]
        
        nodes = [{
            'id': user.id,
            'label': f"{user.first_name} {user.last_name}",
            'type': 'current_user',
            'avatar': user.account.avatar.url if user.account.avatar else None
        }]
        
        edges = []
        
        for sim in similarities:
            related_user = sim.user2
            nodes.append({
                'id': related_user.id,
                'label': f"{related_user.first_name} {related_user.last_name}",
                'type': 'related_user',
                'avatar': related_user.account.avatar.url if related_user.account.avatar else None,
                'similarity_score': sim.similarity_score
            })
            
            edges.append({
                'source': user.id,
                'target': related_user.id,
                'weight': sim.similarity_score,
                'label': f"{sim.similarity_score:.2f}"
            })
        
        return JsonResponse({
            'nodes': nodes,
            'edges': edges,
            'user_id': user.id
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)