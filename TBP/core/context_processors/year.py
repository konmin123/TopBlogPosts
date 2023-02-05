from datetime import datetime


def year(request):
    """Добавляет в контекст переменную year с текущим годом."""
    year_now = datetime.now().year
    return {'year': year_now, 'request': request}
