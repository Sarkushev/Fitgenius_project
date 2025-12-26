from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import openpyxl

from .models import UserProfile, CustomUser, TrainingPlan, Training, Exercise
from .forms import (
    UserProfileForm,
    CustomUserCreationForm,
    CustomAuthenticationForm,
    TrainingForm,
    TrainingExerciseFormset,
)
from .exports import export_profile_pdf_response, export_training_xlsx_response

# Регистрация
class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'training_plans/register.html'
    success_url = reverse_lazy('training_plans:profile_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Authenticate the newly created user so that `backend` is set (required when multiple auth backends are configured)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
        else:
            # Fallback: set backend manually and log in (ensures compatibility when custom backends are present)
            backend = settings.AUTHENTICATION_BACKENDS[0]
            self.object.backend = backend
            login(self.request, self.object)
        messages.success(self.request, f'Добро пожаловать, {self.object.username}! Создайте свой первый профиль.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)

# Создание профиля (только для авторизованных)
@method_decorator(login_required, name='dispatch')
class UserProfileCreateView(CreateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'training_plans/profile_form.html'
    success_url = reverse_lazy('training_plans:profile_list')

    def form_valid(self, form):
        # Проверяем, нет ли уже профиля у пользователя
        if UserProfile.objects.filter(user=self.request.user).exists():
            messages.warning(self.request, 'У вас уже есть профиль. Вы можете его отредактировать.')
            return redirect('training_plans:profile_list')
        
        form.instance.user = self.request.user
        response = super().form_valid(form)
        # Автоматически генерируем тренировочный план после создания профиля
        self.object.generate_training_plan()
        messages.success(self.request, 'Профиль успешно создан! Сгенерирован тренировочный план.')
        return response

# Список профилей
@method_decorator(login_required, name='dispatch')
class UserProfileListView(ListView):
    model = UserProfile
    template_name = 'training_plans/profile_list.html'
    context_object_name = 'profiles'
    
    def get_queryset(self):
        # Показываем только профили текущего пользователя
        return UserProfile.objects.filter(user=self.request.user)

# Редактирование профиля
@method_decorator(login_required, name='dispatch')
class UserProfileUpdateView(UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'training_plans/profile_form.html'
    success_url = reverse_lazy('training_plans:profile_list')
    
    def get_queryset(self):
        # Разрешаем редактировать только свои профили
        return UserProfile.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлен!')
        return super().form_valid(form)

# Удаление профиля
@method_decorator(login_required, name='dispatch')
class UserProfileDeleteView(DeleteView):
    model = UserProfile
    template_name = 'training_plans/profile_confirm_delete.html'
    success_url = reverse_lazy('training_plans:profile_list')
    
    def get_queryset(self):
        # Разрешаем удалять только свои профили
        return UserProfile.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Профиль успешно удален!')
        return super().delete(request, *args, **kwargs)

# Детали профиля
@method_decorator(login_required, name='dispatch')
class UserProfileDetailView(DetailView):
    model = UserProfile
    template_name = 'training_plans/profile_detail.html'
    
    def get_queryset(self):
        # Разрешаем просматривать только свои профили
        return UserProfile.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['training_plans'] = self.object.training_plans.all().order_by('day')
        return context

# Генерация плана
@login_required
def generate_plan_view(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk, user=request.user)
    profile.generate_training_plan()
    messages.success(request, 'Тренировочный план успешно сгенерирован!')
    return redirect('training_plans:profile_detail', pk=pk)


# --------------------------
# User-created Trainings
# --------------------------


class TrainingListView(LoginRequiredMixin, ListView):
    model = Training
    template_name = 'training_plans/training_list.html'
    context_object_name = 'trainings'

    def get_queryset(self):
        return Training.objects.filter(user=self.request.user).order_by('-created_at')


class TrainingCreateView(LoginRequiredMixin, CreateView):
    model = Training
    form_class = TrainingForm
    template_name = 'training_plans/training_form.html'
    success_url = reverse_lazy('training_plans:training_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = TrainingExerciseFormset(self.request.POST)
        else:
            context['formset'] = TrainingExerciseFormset()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        form.instance.user = self.request.user
        response = super().form_valid(form)
        # Save exercises only if the formset is valid or empty
        try:
            valid = formset.is_valid()
        except Exception:
            # If management form missing but no exercise data provided, treat as empty
            if any(f for f in formset.forms if f.has_changed()):
                self.object.delete()
                return self.form_invalid(form)
            valid = False

        if valid:
            formset.instance = self.object
            formset.save()
        messages.success(self.request, 'Тренировка успешно создана!')
        return response


class TrainingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Training
    form_class = TrainingForm
    template_name = 'training_plans/training_form.html'
    success_url = reverse_lazy('training_plans:training_list')

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = TrainingExerciseFormset(self.request.POST, instance=self.object)
        else:
            context['formset'] = TrainingExerciseFormset(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        response = super().form_valid(form)
        try:
            valid = formset.is_valid()
        except Exception:
            # If management form missing but no exercise data provided, treat as empty
            if any(f for f in formset.forms if f.has_changed()):
                return self.form_invalid(form)
            valid = False

        if valid:
            formset.instance = self.object
            formset.save()
        messages.success(self.request, 'Тренировка успешно обновлена!')
        return response


class TrainingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Training
    template_name = 'training_plans/training_detail.html'

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user


class TrainingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Training
    template_name = 'training_plans/training_confirm_delete.html'
    success_url = reverse_lazy('training_plans:training_list')

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user


@login_required
def export_training_xlsx(request, pk):
    training = get_object_or_404(Training, pk=pk, user=request.user)
    return export_training_xlsx_response(training)


# Экспорт в PDF персонального плана (только для владельца)
@login_required
def export_training_plan_pdf(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk, user=request.user)
    # Delegate to helper that builds a PDF response
    return export_profile_pdf_response(profile)

# Домашняя страница
def home_view(request):
    if request.user.is_authenticated:
        return redirect('training_plans:profile_list')
    return render(request, 'training_plans/home.html')