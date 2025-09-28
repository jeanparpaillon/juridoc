all: build

build:
	python setup.py sdist bdist_wheel

win_build:
	docker run \
	--rm \
	-v $(PWD):/src \
	cdrx/pyinstaller-windows:python3 \
	python setup.py build_pyinstaller

clean:
	rm -rf dist build *.egg-info

.PHONY: all clean