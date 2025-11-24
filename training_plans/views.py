from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import UserProfile, TrainingPlan
from .forms import UserProfileForm

class UserProfileListView(ListView):
    model = UserProfile
    template_name = 'training_plans/profile_list.html'
    context_object_name = 'profiles'

class UserProfileCreateView(CreateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'training_plans/profile_form.html'
    success_url = reverse_lazy('training_plans:profile_list')  # ← ИСПРАВЛЕНО: добавлено пространство имен

    def form_valid(self, form):
        response = super().form_valid(form)
        # Автоматически генерируем тренировочный план после создания профиля
        self.object.generate_training_plan()
        return response

class UserProfileUpdateView(UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'training_plans/profile_form.html'
    success_url = reverse_lazy('training_plans:profile_list')  # ← ИСПРАВЛЕНО: добавлено пространство имен

class UserProfileDeleteView(DeleteView):
    model = UserProfile
    template_name = 'training_plans/profile_confirm_delete.html'
    success_url = reverse_lazy('training_plans:profile_list')  # ← ИСПРАВЛЕНО: добавлено пространство имен

class UserProfileDetailView(DetailView):
    model = UserProfile
    template_name = 'training_plans/profile_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['training_plans'] = self.object.training_plans.all()
        return context

def generate_plan_view(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)
    profile.generate_training_plan()
    return redirect('training_plans:profile_detail', pk=pk)  # ← ИСПРАВЛЕНО: добавлено пространство имен