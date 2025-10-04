dev:
	uv run python manage.py runserver

poster:
	uv run python manage.py runposter

tests:
	uv run python manage.py test

migrate-all:
	uv run python manage.py makemigrations
	uv run python manage.py migrate
	uv run python manage.py makemigrations integrations 
	uv run python manage.py migrate integrations 
	uv run python manage.py makemigrations socialsched 
	uv run python manage.py migrate socialsched


purge-migration-dirs:
	rm -rf integrations/migrations
	rm -rf socialsched/migrations


purge-db:
	make purge-migration-dirs
	rm data/db.sqlite3


prep-prod:
	make migrate-all
	uv run python manage.py collectstatic --noinput
	rm -rf staticfiles/django-browser-reload


# Before this run: docker network create web - one-time thing useful for using same proxy for multiple docker apps
# OR you can add caddy proxy inside docker-compose.yml if you are runnig just this app

startproxy:
	docker compose -p proxy -f docker-compose.proxy.yml up -d --force-recreate

startapp:
	docker compose -p app -f docker-compose.yml up -d --force-recreate

start: 
	make startproxy 
	make startapp

stopproxy:
	docker compose -p proxy -f docker-compose.proxy.yml down

stopapp:
	docker compose -p app -f docker-compose.yml down

stop:
	make stopapp
	make stopproxy

build:
	docker compose -p app -f docker-compose.yml build

applogs:
	docker compose -p app -f docker-compose.yml logs imposting-web imposting-cron-poster -ft

proxylogs:
	docker compose -p proxy -f docker-compose.proxy.yml logs external-caddy-proxy -ft

appexec:
	docker compose -p app -f docker-compose.yml exec imposting-web bash