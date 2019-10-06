PY_FILES=$(shell find . -name '*.py' -not -wholename './.*')

build/test_output.txt: $(PY_FILES) build
	python setup.py test 2>&1 | tee build/test_output.txt

build:
	mkdir build

clean:
	git clean -f -X -d

.PHONY: clean
