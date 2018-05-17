all:
	@echo 'For upgrade pip, install btdht and upgrade requests write:'
	@echo 'make install'
	@echo 'If there are troubles try:'
	@echo 'make install2'

install:
	@echo 'install'
	apt-get update
	apt-get install python-pip python-dev build-essential
	pip install --upgrade pip
	pip install --upgrade setuptools
	pip install btdht
	pip install --upgrade requests

install2:
	@echo 'install2'
	apt-get update
	apt-get install python-pip python-dev build-essential
	pip install --upgrade pip
	pip install --upgrade setuptools
	pip install --ignore-installed btdht
	pip install --ignore-installed requests
