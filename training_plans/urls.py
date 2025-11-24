from django.urls import path
from . import views

app_name = 'training_plans'

urlpatterns = [
    path('', views.UserProfileListView.as_view(), name='profile_list'),
    path('create/', views.UserProfileCreateView.as_view(), name='profile_create'),
    path('<int:pk>/', views.UserProfileDetailView.as_view(), name='profile_detail'),
    path('<int:pk>/update/', views.UserProfileUpdateView.as_view(), name='profile_update'),
    path('<int:pk>/delete/', views.UserProfileDeleteView.as_view(), name='profile_delete'),
    path('<int:pk>/generate-plan/', views.generate_plan_view, name='generate_plan'),
]