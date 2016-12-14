all: clean setup_db
	python3 manage.py runscript load_config --traceback
	sudo python3 manage.py runserver 0.0.0.0:10411

test: clean setup_db
	python3 manage.py test
	sudo python3 manage.py runserver 0.0.0.0:10411

setup_db:
	python3 manage.py makemigrations
	python3 manage.py makemigrations website
	python3 manage.py migrate

clean:
	-ps aux | grep manage.py | awk '/[ \t]/ {print $2}' | xargs sudo kill -9
	-ls | grep '^task_manager_lock_' | xargs rm
	-ls / | grep '^tellina_session_' | xargs sudo bash delete_filesystem.bash
	-sudo docker rm -f `sudo docker ps -q -a`
	rm -rf db.sqlite3 website/migrations
