release: python manage.py migrate
web: gunicorn wsgi.py --preload --workers 1
