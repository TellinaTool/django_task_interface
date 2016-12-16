# This Makefile wraps commands used to setup, test, and run the server.

run: build_image clean setup_db
	# Load config.json into database.
	python3 manage.py runscript load_config --traceback
	# Run server.
	sudo python3 manage.py runserver 0.0.0.0:10411

test: build_image clean setup_db
	# Run automated tests.
	python3 manage.py test
	# Run server.
	sudo python3 manage.py runserver 0.0.0.0:10411

# Build the Docker image. (Needs to be done each time server is run since
# changes may have been made to the image.)
build_image:
	sudo docker build -t tellina docker_image

# Setup database tables.
setup_db:
	python3 manage.py makemigrations
	python3 manage.py makemigrations website
	python3 manage.py migrate

# Clean up environment left by prior server run.
clean:
	# Kill existing server process.
	-ps aux | grep manage.py | awk '/[ \t]/ {print $2}' | xargs sudo kill -9
	# Remove lock files.
	-ls | grep '^task_manager_lock_' | xargs rm
	# Delete virtual filesystems.
	-ls / | grep '^tellina_session_' | xargs sudo bash delete_filesystem.bash
	# Destroy Docker containers.
	-sudo docker rm -f `sudo docker ps -q -a`
	# Destroy database and migrations.
	rm -rf db.sqlite3 website/migrations
