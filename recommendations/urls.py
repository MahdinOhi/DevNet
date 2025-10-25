from django.urls import path
from . import views

urlpatterns = [
    # API endpoints for recommendations
    path('api/users/<int:user_id>/related/', views.get_related_users, name='related-users'),
    path('api/projects/<int:project_id>/related/', views.get_related_projects, name='related-projects'),
    path('api/users/<int:user_id>/recommendations/', views.get_user_recommendations, name='user-recommendations'),
    path('api/users/<int:user_id>/graph/', views.get_similarity_graph, name='similarity-graph'),
    path('api/update-similarities/', views.update_similarities, name='update-similarities'),
]
