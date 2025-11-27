from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm

app_name = 'training_plans'

urlpatterns = [
    # Главная страница
    path('', views.home_view, name='home'),
    
    # Аутентификация
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='training_plans/login.html',
        authentication_form=CustomAuthenticationForm,
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='training_plans:home'), name='logout'),
    
    # Профили
    path('profiles/', views.UserProfileListView.as_view(), name='profile_list'),
    path('profiles/create/', views.UserProfileCreateView.as_view(), name='profile_create'),
    path('profiles/<int:pk>/', views.UserProfileDetailView.as_view(), name='profile_detail'),
    path('profiles/<int:pk>/update/', views.UserProfileUpdateView.as_view(), name='profile_update'),
    path('profiles/<int:pk>/delete/', views.UserProfileDeleteView.as_view(), name='profile_delete'),
    path('profiles/<int:pk>/generate-plan/', views.generate_plan_view, name='generate_plan'),
]