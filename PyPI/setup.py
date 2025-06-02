from setuptools import setup, find_packages
import os

# Read the contents of your README file with fallback
this_directory = os.path.abspath(os.path.dirname(__file__))

# Try to read README.md from current directory first, then fallback
readme_path = os.path.join(this_directory, 'README.md')
long_description = "A YouTube downloader app with GUI"  # Fallback description

if os.path.exists(readme_path):
    try:
        with open(readme_path, encoding='utf-8') as f:
            long_description = f.read()
    except Exception:
        pass

# Try to read LICENSE file
license_content = "MIT"
license_path = os.path.join(this_directory, 'LICENSE')

setup(
    name="hwytvidgrabber",
    version="1.4.2",
    description="A YouTube downloader app with GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MalikHw",
    author_email="help.malicorporation@gmail.com",
    url="https://github.com/MalikHw/HwYtVidGrabber",
    license="MIT",
    packages=find_packages(),
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
            "twine>=4.0.0",
            "build>=0.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hwytvidgrabber=hwytvidgrabber:main",
        ],
        "gui_scripts": [
            "hwytvidgrabber-gui=hwytvidgrabber:main",
        ],
    },
    include_package_data=True,
    package_data={
        "hwytvidgrabber": ["*.png", "*.ico"],
    },
    project_urls={
        "Bug Reports": "https://github.com/MalikHw/HwYtVidGrabber/issues",
        "Source": "https://github.com/MalikHw/HwYtVidGrabber",
        "Funding": "https://www.ko-fi.com/MalikHw47",
    },
)
