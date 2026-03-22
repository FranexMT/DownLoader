from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="DownLoader",
    version="2.1.0",
    description="Ethereal Downloader - Advanced Download Manager with Global Glassmorphism GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DownLoader Team",
    author_email="team@downloader.local",
    url="https://github.com/usuario/DownLoader",
    license="MIT",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'downloader=src.cli.main:main',
            'downloader-gui=src.gui:run_gui',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
