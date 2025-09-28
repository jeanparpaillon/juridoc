all: build

build:
	python -m build

exe:
	pyinstaller juridoc.spec

win_exe:
	docker run \
	  --rm \
	  -v $(PWD):/src \
	  cdrx/pyinstaller-windows:python3 \
	  pyinstaller juridoc.spec

clean:
	rm -rf dist build *.egg-info

.PHONY: all clean