from setuptools import setup, find_packages
import os

# Read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="hwyvidgrabber",
    version="1.4.1",
    description="A YouTube downloader app with GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MalikHw",
    author_email="help.malicorporation@gmail.com",
    url="https://github.com/MalikHw/HwYtVidGrabber",
    license="MIT",
    packages=find_packages(),
    py_modules=["hwyvidgrabber"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Internet :: WWW/HTTP",
        "Environment :: X11 Applications :: Qt",
    ],
    keywords="youtube downloader video audio mp3 mp4 gui pyqt6",
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.4.0",
        "yt-dlp>=2023.1.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hwyvidgrabber=HwYtVidGrabber:main",
        ],
        "gui_scripts": [
            "hwyvidgrabber-gui=HwYtVidGrabber:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.png", "*.ico", "*.md", "LICENSE"],
    },
    project_urls={
        "Bug Reports": "https://github.com/MalikHw/HwYtVidGrabber/issues",
        "Source": "https://github.com/MalikHw/HwYtVidGrabber",
        "Funding": "https://www.ko-fi.com/MalikHw47",
    },
)