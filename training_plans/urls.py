from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.views.generic import RedirectView
from django.urls import reverse_lazy
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
    # Short redirect for convenience / common typo (e.g. user types /l)
    path('l', RedirectView.as_view(url=reverse_lazy('training_plans:login'), permanent=False)),
    path('logout/', auth_views.LogoutView.as_view(next_page='training_plans:home'), name='logout'),
    
    # Профили
    path('profiles/', views.UserProfileListView.as_view(), name='profile_list'),
    path('profiles/create/', views.UserProfileCreateView.as_view(), name='profile_create'),
    path('profiles/<int:pk>/', views.UserProfileDetailView.as_view(), name='profile_detail'),
    path('profiles/<int:pk>/update/', views.UserProfileUpdateView.as_view(), name='profile_update'),
    path('profiles/<int:pk>/delete/', views.UserProfileDeleteView.as_view(), name='profile_delete'),
    path('profiles/<int:pk>/generate-plan/', views.generate_plan_view, name='generate_plan'),
    path('profiles/<int:pk>/export-pdf/', views.export_training_plan_pdf, name='export_pdf'),
    # User-created trainings CRUD
    path('trainings/', views.TrainingListView.as_view(), name='training_list'),
    path('trainings/create/', views.TrainingCreateView.as_view(), name='training_create'),
    path('trainings/<int:pk>/', views.TrainingDetailView.as_view(), name='training_detail'),
    path('trainings/<int:pk>/update/', views.TrainingUpdateView.as_view(), name='training_update'),
    path('trainings/<int:pk>/delete/', views.TrainingDeleteView.as_view(), name='training_delete'),
    path('trainings/<int:pk>/export/', views.export_training_xlsx, name='training_export'),
]