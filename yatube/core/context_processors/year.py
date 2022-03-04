import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    now = datetime.date.today()
    year = now.year
    return {
        'year': year,
    }
