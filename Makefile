dev:
	python manage.py runserver

cron:
	python manage.py runposter

web:
	uvicorn core.asgi:application --host 0.0.0.0 --port 8000

migrate-all:
	python manage.py makemigrations
	python manage.py migrate
	python manage.py makemigrations integrations 
	python manage.py migrate integrations 
	python manage.py makemigrations socialsched 
	python manage.py migrate socialsched


purge-migration-dirs:
	rm -rf integrations/migrations
	rm -rf socialsched/migrations


purge-db:
	make purge-migration-dirs
	rm data/db.sqlite
