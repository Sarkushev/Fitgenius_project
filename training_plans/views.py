from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .models import UserProfile, CustomUser, TrainingPlan
from .forms import UserProfileForm, CustomUserCreationForm, CustomAuthenticationForm

# Регистрация
class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'training_plans/register.html'
    success_url = reverse_lazy('training_plans:profile_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
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


# Экспорт в PDF персонального плана (только для владельца)
@login_required
def export_training_plan_pdf(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk, user=request.user)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Заголовок
    p.setFont('Helvetica-Bold', 16)
    p.drawString(40, height - 50, f"Тренировочный план для: {profile.user.email}")
    p.setFont('Helvetica', 12)
    p.drawString(40, height - 70, f"Возраст: {profile.age}  Рост: {profile.height} см  Вес: {profile.weight} кг")
    p.drawString(40, height - 90, f"Цель: {profile.get_goal_display}  Уровень: {profile.get_fitness_level_display}")

    y = height - 120
    p.setFont('Helvetica-Bold', 14)
    current_day = None
    plans = profile.training_plans.all().order_by('day')
    for item in plans:
        if y < 100:
            p.showPage()
            y = height - 50
        if current_day != item.get_day_display():
            current_day = item.get_day_display()
            p.setFont('Helvetica-Bold', 12)
            p.drawString(40, y, current_day)
            y -= 18
        p.setFont('Helvetica', 11)
        line = f"- {item.exercise_name} | Подходы: {item.sets} | Повторы: {item.reps} | Отдых: {item.rest_time}"
        p.drawString(50, y, line)
        y -= 16
        if item.notes:
            p.setFont('Helvetica-Oblique', 10)
            p.drawString(60, y, f"Примечание: {item.notes}")
            y -= 14

    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

# Домашняя страница
def home_view(request):
    if request.user.is_authenticated:
        return redirect('training_plans:profile_list')
    return render(request, 'training_plans/home.html')