from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Создаем кастомную модель пользователя
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    
    def __str__(self):
        return self.email

class UserProfile(models.Model):
    GOAL_CHOICES = [
        ('weight_loss', 'Похудение'),
        ('muscle_gain', 'Набор мышечной массы'),
        ('strength', 'Развитие силы'),
        ('endurance', 'Выносливость'),
        ('health', 'Общее оздоровление'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Мужчина'),
        ('female', 'Женщина'),
    ]
    
    # Связываем профиль с пользователем
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name="Пользователь"
    )
    
    # Персональные данные
    age = models.IntegerField(
        validators=[MinValueValidator(16), MaxValueValidator(80)],
        verbose_name="Возраст"
    )
    height = models.FloatField(verbose_name="Рост (см)")
    weight = models.FloatField(verbose_name="Вес (кг)")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name="Пол")
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES, verbose_name="Цель")
    fitness_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Начинающий'),
            ('intermediate', 'Средний'),
            ('advanced', 'Продвинутый')
        ],
        verbose_name="Уровень подготовки"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_bmi(self):
        """Расчет индекса массы тела"""
        return round(self.weight / ((self.height / 100) ** 2), 1)

    def __str__(self):
        return f"{self.user.username} - {self.get_goal_display()}"

    def generate_training_plan(self):
        """Генерация персонального тренировочного плана на основе данных пользователя"""
        # Очищаем старый план
        self.training_plans.all().delete()
        
        bmi = self.calculate_bmi()
        
        # Базовая логика в зависимости от цели и ИМТ
        if self.goal == 'weight_loss':
            plans = self._generate_weight_loss_plan(bmi)
        elif self.goal == 'muscle_gain':
            plans = self._generate_muscle_gain_plan(bmi)
        elif self.goal == 'strength':
            plans = self._generate_strength_plan(bmi)
        else:
            plans = self._generate_health_plan(bmi)
        
        # Создаем тренировочные дни
        for day, exercises in plans.items():
            for exercise in exercises:
                TrainingPlan.objects.create(
                    user_profile=self,
                    day=day,
                    exercise_name=exercise['name'],
                    sets=exercise['sets'],
                    reps=exercise['reps'],
                    rest_time=exercise['rest'],
                    notes=exercise.get('notes', '')
                )
    
    def _generate_weight_loss_plan(self, bmi):
        """Генерация плана для похудения"""
        base_plan = {
            'monday': [
                {'name': 'Бег на дорожке', 'sets': 1, 'reps': '20-30 мин', 'rest': '—'},
                {'name': 'Приседания', 'sets': 3, 'reps': '15-20', 'rest': '45 сек'},
                {'name': 'Выпады', 'sets': 3, 'reps': '12-15 на ногу', 'rest': '45 сек'},
            ],
            'wednesday': [
                {'name': 'Эллиптический тренажер', 'sets': 1, 'reps': '25-35 мин', 'rest': '—'},
                {'name': 'Жим гантелей лежа', 'sets': 3, 'reps': '12-15', 'rest': '45 сек'},
                {'name': 'Тяга верхнего блока', 'sets': 3, 'reps': '12-15', 'rest': '45 сек'},
            ],
            'friday': [
                {'name': 'Велотренажер', 'sets': 1, 'reps': '20-30 мин', 'rest': '—'},
                {'name': 'Планка', 'sets': 3, 'reps': '30-60 сек', 'rest': '30 сек'},
                {'name': 'Скручивания', 'sets': 3, 'reps': '15-20', 'rest': '30 сек'},
            ]
        }
        return self._adjust_plan_by_level(base_plan)
    
    def _generate_muscle_gain_plan(self, bmi):
        """Генерация плана для набора массы"""
        base_plan = {
            'monday': [  # Грудь, трицепс
                {'name': 'Жим штанги лежа', 'sets': 4, 'reps': '8-12', 'rest': '90 сек'},
                {'name': 'Разводка гантелей', 'sets': 3, 'reps': '10-15', 'rest': '60 сек'},
                {'name': 'Отжимания на брусьях', 'sets': 3, 'reps': '8-12', 'rest': '75 сек'},
            ],
            'tuesday': [  # Спина, бицепс
                {'name': 'Становая тяга', 'sets': 4, 'reps': '6-10', 'rest': '120 сек'},
                {'name': 'Подтягивания', 'sets': 3, 'reps': 'макс', 'rest': '90 сек'},
                {'name': 'Тяга штанги в наклоне', 'sets': 3, 'reps': '8-12', 'rest': '75 сек'},
            ],
            'thursday': [  # Ноги, плечи
                {'name': 'Приседания со штангой', 'sets': 4, 'reps': '8-12', 'rest': '120 сек'},
                {'name': 'Жим гантелей сидя', 'sets': 3, 'reps': '10-15', 'rest': '60 сек'},
                {'name': 'Подъем на носки', 'sets': 4, 'reps': '15-20', 'rest': '45 сек'},
            ]
        }
        return self._adjust_plan_by_level(base_plan)
    
    def _adjust_plan_by_level(self, plan):
        """Корректировка плана по уровню подготовки"""
        if self.fitness_level == 'beginner':
            # Уменьшаем объем для новичков
            adjusted_plan = {}
            for day, exercises in plan.items():
                adjusted_plan[day] = []
                for exercise in exercises:
                    adj_exercise = exercise.copy()
                    adj_exercise['sets'] = max(2, exercise['sets'] - 1)
                    if 'мин' in exercise['reps']:
                        adj_exercise['reps'] = exercise['reps'].replace('25-35', '15-25').replace('20-30', '10-20')
                    adjusted_plan[day].append(adj_exercise)
            return adjusted_plan
        return plan
    
    def _generate_strength_plan(self, bmi):
        """Генерация плана для развития силы"""
        base_plan = {
            'monday': [
                {'name': 'Приседания со штангой', 'sets': 5, 'reps': '3-5', 'rest': '180 сек'},
                {'name': 'Жим ногами', 'sets': 3, 'reps': '6-8', 'rest': '120 сек'},
            ],
            'wednesday': [
                {'name': 'Жим штанги лежа', 'sets': 5, 'reps': '3-5', 'rest': '180 сек'},
                {'name': 'Армейский жим', 'sets': 3, 'reps': '5-8', 'rest': '120 сек'},
            ],
            'friday': [
                {'name': 'Становая тяга', 'sets': 5, 'reps': '3-5', 'rest': '180 сек'},
                {'name': 'Тяга штанги в наклоне', 'sets': 3, 'reps': '5-8', 'rest': '120 сек'},
            ]
        }
        return self._adjust_plan_by_level(base_plan)
    
    def _generate_health_plan(self, bmi):
        """Генерация плана для общего оздоровления"""
        base_plan = {
            'monday': [
                {'name': 'Ходьба/Бег', 'sets': 1, 'reps': '20-30 мин', 'rest': '—'},
                {'name': 'Приседания с собственным весом', 'sets': 3, 'reps': '12-15', 'rest': '60 сек'},
            ],
            'wednesday': [
                {'name': 'Плавание/Велосипед', 'sets': 1, 'reps': '25-35 мин', 'rest': '—'},
                {'name': 'Отжимания от пола', 'sets': 3, 'reps': '8-12', 'rest': '60 сек'},
            ],
            'friday': [
                {'name': 'Йога/Растяжка', 'sets': 1, 'reps': '20-30 мин', 'rest': '—'},
                {'name': 'Планка', 'sets': 3, 'reps': '30-45 сек', 'rest': '45 сек'},
            ]
        }
        return self._adjust_plan_by_level(base_plan)


class TrainingPlan(models.Model):
    DAY_CHOICES = [
        ('monday', 'Понедельник'),
        ('tuesday', 'Вторник'),
        ('wednesday', 'Среда'),
        ('thursday', 'Четверг'),
        ('friday', 'Пятница'),
        ('saturday', 'Суббота'),
        ('sunday', 'Воскресенье'),
    ]
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='training_plans')
    day = models.CharField(max_length=10, choices=DAY_CHOICES, verbose_name="День недели")
    exercise_name = models.CharField(max_length=200, verbose_name="Упражнение")
    sets = models.IntegerField(verbose_name="Подходы")
    reps = models.CharField(max_length=50, verbose_name="Повторения")
    rest_time = models.CharField(max_length=50, verbose_name="Время отдыха", default="60 сек")
    notes = models.TextField(blank=True, verbose_name="Примечания")

    class Meta:
        ordering = ['day']

    def __str__(self):
        return f"{self.get_day_display()} - {self.exercise_name}"