python manage.py makemigrations --no-input
python manage.py migrate --no-input
python manage.py load_data -e
python manage.py create_superuser -u
python manage.py collectstatic --no-input
cp -r /app/collected_static/. /static/static/
cp -r /app/data/recipes/. /app/media/recipes/

gunicorn backend_foodgram.wsgi:application --bind 0.0.0.0:8000
 