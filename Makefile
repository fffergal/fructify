build/test: test_passenger_wsgi.py passenger_wsgi.py build/venv/bin/tox
	. build/venv/bin/activate
	tox
	touch build/test

build/reload: build/put
	ssh "$(SSH_USER)@ifttt.bfot.co.uk" pkill python || true
	touch build/reload

build/put: ftp.txt build/test
	sftp -b ftp.txt "$(SSH_USER)@ifttt.bfot.co.uk"
	touch build/put

build/venv/bin/tox: build/venv
	. build/venv/bin/activate
	pip install tox

build/venv:
	virtualenv build/venv

build:
	mkdir build

clean:
	git clean -f -X -d

.PHONY: clean
