from setuptools import setup, find_packages
import os

NAME = "webmonitor"
VERSION = "0.1.0"
DESCRIPTION = "A monitoring tool for websites and databases"
AUTHOR = "Barooon165"
AUTHOR_EMAIL = "ongiabaoit22@gmail.com"

here = os.path.abspath(os.path.dirname(__file__))

# Read the requirements from requirements.txt file
def read_requirements():
    requirements_path = os.path.join(here, "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

# Read the contents of your README file
def read_long_description():
    readme_path = os.path.join(here, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return DESCRIPTION

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "webmonitor=webmonitor.cli:main",
            "webmonitor-daemon=webmonitor.daemon:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    include_package_data=True,
)
