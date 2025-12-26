from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile, CustomUser
from .models import Training, Exercise
from django.forms import inlineformset_factory

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш email'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя пользователя'})
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Подтвердите пароль'}),
        }

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'})
    )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age', 'height', 'weight', 'gender', 'goal', 'fitness_level']
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': '16', 'max': '80'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '100', 'max': '250'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '30', 'max': '300'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'goal': forms.Select(attrs={'class': 'form-control'}),
            'fitness_level': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'age': 'Возраст (лет)',
            'height': 'Рост (см)',
            'weight': 'Вес (кг)',
            'gender': 'Пол',
            'goal': 'Цель тренировок',
            'fitness_level': 'Уровень подготовки',
        }


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название тренировки'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание (опционально)'}),
        }


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ['day', 'name', 'sets', 'reps', 'rest_time', 'notes']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sets': forms.NumberInput(attrs={'class': 'form-control'}),
            'reps': forms.TextInput(attrs={'class': 'form-control'}),
            'rest_time': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


TrainingExerciseFormset = inlineformset_factory(
    Training,
    Exercise,
    form=ExerciseForm,
    extra=1,
    can_delete=True
)