from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import openpyxl


def export_profile_pdf_response(profile):
    """Return HttpResponse with a PDF for a given `UserProfile` instance."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Заголовок
    p.setFont('Helvetica-Bold', 16)
    p.drawString(40, height - 50, f"Тренировочный план для: {profile.user.email}")
    p.setFont('Helvetica', 12)
    p.drawString(40, height - 70, f"Возраст: {profile.age}  Рост: {profile.height} см  Вес: {profile.weight} кг")
    p.drawString(40, height - 90, f"Цель: {profile.get_goal_display()}  Уровень: {profile.get_fitness_level_display()}")

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
    # Return as an attachment with a filename so browsers download the PDF
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"training_plan_{profile.user.username}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_training_xlsx_response(training):
    """Return HttpResponse with an .xlsx file for a given `Training` instance."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = training.title[:30]

    # Header
    ws.append(['День', 'Упражнение', 'Подходы', 'Повторы', 'Отдых', 'Примечания'])

    for ex in training.exercises.all():
        ws.append([ex.get_day_display(), ex.name, ex.sets, ex.reps, ex.rest_time, ex.notes])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"training_{training.pk}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
