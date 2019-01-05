release: python manage.py migrate
web: gunicorn wsgi:application --preload --workers 1
