from django.contrib import admin
from .models import UserSimilarity, ProjectSimilarity


@admin.register(UserSimilarity)
class UserSimilarityAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'similarity_score', 'similarity_type', 'created_at']
    list_filter = ['similarity_type', 'created_at']
    search_fields = ['user1__username', 'user2__username']
    ordering = ['-similarity_score']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProjectSimilarity)
class ProjectSimilarityAdmin(admin.ModelAdmin):
    list_display = ['project1', 'project2', 'similarity_score', 'similarity_type', 'created_at']
    list_filter = ['similarity_type', 'created_at']
    search_fields = ['project1__title', 'project2__title']
    ordering = ['-similarity_score']
    readonly_fields = ['created_at', 'updated_at']