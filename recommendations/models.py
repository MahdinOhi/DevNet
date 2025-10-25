from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
import json
from collections import defaultdict
from typing import List, Dict, Tuple
import math


class UserSimilarity(models.Model):
    """Graph-based model for storing user similarity relationships"""
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='similarity_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='similarity_as_user2')
    similarity_score = models.FloatField(default=0.0)
    similarity_type = models.CharField(max_length=50, default='skill_based')  # skill_based, project_based, location_based, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user1', 'user2']
        ordering = ['-similarity_score']
    
    def __str__(self):
        return f"{self.user1.username} -> {self.user2.username} ({self.similarity_score:.2f})"


class ProjectSimilarity(models.Model):
    """Graph-based model for storing project similarity relationships"""
    project1 = models.ForeignKey('main.Project', on_delete=models.CASCADE, related_name='similarity_as_project1')
    project2 = models.ForeignKey('main.Project', on_delete=models.CASCADE, related_name='similarity_as_project2')
    similarity_score = models.FloatField(default=0.0)
    similarity_type = models.CharField(max_length=50, default='tag_based')  # tag_based, skill_based, user_based
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['project1', 'project2']
        ordering = ['-similarity_score']
    
    def __str__(self):
        return f"{self.project1.title} -> {self.project2.title} ({self.similarity_score:.2f})"


class RecommendationEngine:
    """Graph-based recommendation engine using similarity algorithms"""
    
    @staticmethod
    def calculate_user_similarity(user1: User, user2: User) -> float:
        """Calculate similarity between two users using multiple factors"""
        if user1 == user2:
            return 0.0
        
        # Get user accounts
        account1 = user1.account
        account2 = user2.account
        
        # Initialize similarity components
        skill_similarity = 0.0
        project_similarity = 0.0
        location_similarity = 0.0
        experience_similarity = 0.0
        tech_stack_similarity = 0.0
        
        # 1. Skill-based similarity (Jaccard similarity)
        skills1 = set(account1.skill_set.values_list('name', flat=True))
        skills2 = set(account2.skill_set.values_list('name', flat=True))
        
        if skills1 or skills2:
            intersection = len(skills1.intersection(skills2))
            union = len(skills1.union(skills2))
            skill_similarity = intersection / union if union > 0 else 0.0
        
        # 2. Project-based similarity
        projects1 = set(user1.project_set.values_list('title', flat=True))
        projects2 = set(user2.project_set.values_list('title', flat=True))
        
        if projects1 or projects2:
            intersection = len(projects1.intersection(projects2))
            union = len(projects1.union(projects2))
            project_similarity = intersection / union if union > 0 else 0.0
        
        # 3. Location similarity
        if account1.location and account2.location:
            location1 = account1.location.lower().strip()
            location2 = account2.location.lower().strip()
            if location1 == location2:
                location_similarity = 1.0
            elif location1 in location2 or location2 in location1:
                location_similarity = 0.5
        
        # 4. Experience level similarity
        if account1.experience_level == account2.experience_level:
            experience_similarity = 1.0
        else:
            # Adjacent levels get partial similarity
            levels = ['junior', 'mid', 'senior']
            idx1 = levels.index(account1.experience_level)
            idx2 = levels.index(account2.experience_level)
            if abs(idx1 - idx2) == 1:
                experience_similarity = 0.5
        
        # 5. Technology stack similarity
        if account1.technology_stack and account2.technology_stack:
            tech1 = set(tech.strip().lower() for tech in account1.technology_stack.split(','))
            tech2 = set(tech.strip().lower() for tech in account2.technology_stack.split(','))
            
            if tech1 or tech2:
                intersection = len(tech1.intersection(tech2))
                union = len(tech1.union(tech2))
                tech_stack_similarity = intersection / union if union > 0 else 0.0
        
        # Weighted combination of similarities
        weights = {
            'skill': 0.4,
            'project': 0.2,
            'location': 0.1,
            'experience': 0.1,
            'tech_stack': 0.2
        }
        
        total_similarity = (
            skill_similarity * weights['skill'] +
            project_similarity * weights['project'] +
            location_similarity * weights['location'] +
            experience_similarity * weights['experience'] +
            tech_stack_similarity * weights['tech_stack']
        )
        
        return total_similarity
    
    @staticmethod
    def calculate_project_similarity(project1, project2) -> float:
        """Calculate similarity between two projects"""
        if project1 == project2:
            return 0.0
        
        # 1. Tag-based similarity
        tags1 = set(tag.strip().lower() for tag in project1.tags.split(',') if project1.tags)
        tags2 = set(tag.strip().lower() for tag in project2.tags.split(',') if project2.tags)
        
        tag_similarity = 0.0
        if tags1 or tags2:
            intersection = len(tags1.intersection(tags2))
            union = len(tags1.union(tags2))
            tag_similarity = intersection / union if union > 0 else 0.0
        
        # 2. User-based similarity (similar users work on similar projects)
        user1_skills = set(project1.user.account.skill_set.values_list('name', flat=True))
        user2_skills = set(project2.user.account.skill_set.values_list('name', flat=True))
        
        user_similarity = 0.0
        if user1_skills or user2_skills:
            intersection = len(user1_skills.intersection(user2_skills))
            union = len(user1_skills.union(user2_skills))
            user_similarity = intersection / union if union > 0 else 0.0
        
        # 3. Description similarity (basic keyword matching)
        desc1_words = set(project1.description.lower().split())
        desc2_words = set(project2.description.lower().split())
        
        desc_similarity = 0.0
        if desc1_words or desc2_words:
            intersection = len(desc1_words.intersection(desc2_words))
            union = len(desc1_words.union(desc2_words))
            desc_similarity = intersection / union if union > 0 else 0.0
        
        # Weighted combination
        weights = {
            'tag': 0.5,
            'user': 0.3,
            'description': 0.2
        }
        
        total_similarity = (
            tag_similarity * weights['tag'] +
            user_similarity * weights['user'] +
            desc_similarity * weights['description']
        )
        
        return total_similarity
    
    @staticmethod
    def get_related_users(user: User, limit: int = 5) -> List[Tuple[User, float]]:
        """Get related users based on similarity graph"""
        cache_key = f"related_users_{user.id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get or calculate similarities
        similarities = UserSimilarity.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        ).order_by('-similarity_score')[:limit * 2]
        
        related_users = []
        for sim in similarities:
            related_user = sim.user2 if sim.user1 == user else sim.user1
            if related_user != user:
                related_users.append((related_user, sim.similarity_score))
        
        # If not enough cached similarities, calculate new ones
        if len(related_users) < limit:
            all_users = User.objects.exclude(id=user.id).select_related('account').prefetch_related('account__skill_set')
            
            for other_user in all_users:
                if len(related_users) >= limit:
                    break
                
                # Check if we already have this user
                if any(ru[0] == other_user for ru in related_users):
                    continue
                
                similarity = RecommendationEngine.calculate_user_similarity(user, other_user)
                if similarity > 0.1:  # Only include users with meaningful similarity
                    related_users.append((other_user, similarity))
        
        # Sort by similarity score
        related_users.sort(key=lambda x: x[1], reverse=True)
        related_users = related_users[:limit]
        
        # Cache the result for 1 hour
        cache.set(cache_key, related_users, 3600)
        
        return related_users
    
    @staticmethod
    def get_related_projects(project, limit: int = 5) -> List[Tuple]:
        """Get related projects based on similarity graph"""
        cache_key = f"related_projects_{project.id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get or calculate similarities
        similarities = ProjectSimilarity.objects.filter(
            models.Q(project1=project) | models.Q(project2=project)
        ).order_by('-similarity_score')[:limit * 2]
        
        related_projects = []
        for sim in similarities:
            related_project = sim.project2 if sim.project1 == project else sim.project1
            if related_project != project:
                related_projects.append((related_project, sim.similarity_score))
        
        # If not enough cached similarities, calculate new ones
        if len(related_projects) < limit:
            from main.models import Project
            all_projects = Project.objects.exclude(id=project.id).select_related('user')
            
            for other_project in all_projects:
                if len(related_projects) >= limit:
                    break
                
                # Check if we already have this project
                if any(rp[0] == other_project for rp in related_projects):
                    continue
                
                similarity = RecommendationEngine.calculate_project_similarity(project, other_project)
                if similarity > 0.1:  # Only include projects with meaningful similarity
                    related_projects.append((other_project, similarity))
        
        # Sort by similarity score
        related_projects.sort(key=lambda x: x[1], reverse=True)
        related_projects = related_projects[:limit]
        
        # Cache the result for 1 hour
        cache.set(cache_key, related_projects, 3600)
        
        return related_projects
    
    @staticmethod
    def update_similarities():
        """Update all user and project similarities (can be run as a background task)"""
        from main.models import Project
        
        # Update user similarities
        users = User.objects.select_related('account').prefetch_related('account__skill_set')
        for i, user1 in enumerate(users):
            for user2 in users[i+1:]:
                similarity = RecommendationEngine.calculate_user_similarity(user1, user2)
                if similarity > 0.1:
                    UserSimilarity.objects.update_or_create(
                        user1=user1, user2=user2,
                        defaults={'similarity_score': similarity}
                    )
                    UserSimilarity.objects.update_or_create(
                        user1=user2, user2=user1,
                        defaults={'similarity_score': similarity}
                    )
        
        # Update project similarities
        projects = Project.objects.select_related('user').prefetch_related('user__account__skill_set')
        for i, project1 in enumerate(projects):
            for project2 in projects[i+1:]:
                similarity = RecommendationEngine.calculate_project_similarity(project1, project2)
                if similarity > 0.1:
                    ProjectSimilarity.objects.update_or_create(
                        project1=project1, project2=project2,
                        defaults={'similarity_score': similarity}
                    )
                    ProjectSimilarity.objects.update_or_create(
                        project1=project2, project2=project1,
                        defaults={'similarity_score': similarity}
                    )