from django.contrib import admin
from .models import CustomUser, UserProfile, TrainingPlan, Training, Exercise


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
	list_display = ('email', 'username', 'is_staff', 'is_active')
	search_fields = ('email', 'username')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'age', 'height', 'weight', 'goal', 'fitness_level')


@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
	list_display = ('user_profile', 'day', 'exercise_name', 'sets')


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
	list_display = ('title', 'user', 'created_at')
	search_fields = ('title',)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
	list_display = ('training', 'day', 'name', 'sets', 'reps')

