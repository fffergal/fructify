PY_FILES=$(shell find . -name '*.py' -not -wholename './.*')

build/test_output.txt: tmpdir:=$(shell mktemp -d)
build/test_output.txt: $(PY_FILES) build
	mkfifo $(tmpdir)/testfifo
	( tee build/test_output.txt < $(tmpdir)/testfifo ; rm -rf $(tmpdir) ) &
	python setup.py test > $(tmpdir)/testfifo 2>&1

build:
	mkdir build

clean:
	git clean -f -X -d

.PHONY: clean
