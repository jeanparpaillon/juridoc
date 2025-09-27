from setuptools import setup, find_packages

setup(
    name="juridoc",
    version="0.1.0",
    description="Juridoc document and source management app",
    author="Your Name",
    packages=find_packages(),
    py_modules=["juridoc", "gui", "cli"],
    install_requires=[
        "pyexcel",
        "pyexcel-ods3",
        "pyexcel-xlsx",
        "odfdo",
        "pypdf",
        "jinja2",
        "PySide6",
    ],
    entry_points={
        "console_scripts": [
            "juridoc=cli:main"
        ],
        "gui_scripts": [
            "juridoc-gui=gui:main"
        ]
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
