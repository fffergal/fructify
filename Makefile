# virtualenvs have hard coded absolute paths in them. Use a hash of pwd so you
# can run both make and circleci local execute, which has the project in a
# different path in the container. tox.ini uses it too so export.
PWD_HASH := $(shell pwd | md5sum | awk '{print $$1}')
export PWD_HASH

build/test: test_passenger_wsgi.py passenger_wsgi.py build/venv-$(PWD_HASH)/bin/tox
	. build/venv-$(PWD_HASH)/bin/activate && tox
	touch build/test

build/reload: build/put
	ssh "$(SSH_USER)@ifttt.bfot.co.uk" pkill python || true
	touch build/reload

build/put: ftp.txt build/test
	sftp -b ftp.txt "$(SSH_USER)@ifttt.bfot.co.uk"
	touch build/put

build/venv-$(PWD_HASH)/bin/tox: build/venv-$(PWD_HASH)
	. build/venv-$(PWD_HASH)/bin/activate && pip install tox

build/venv-$(PWD_HASH):
	virtualenv build/venv-$(PWD_HASH)

build:
	mkdir build

clean:
	git clean -f -X -d

.PHONY: clean
