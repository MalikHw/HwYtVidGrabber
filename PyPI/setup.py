from setuptools import setup, find_packages
import os

# Read the contents of your README file with fallback
this_directory = os.path.abspath(os.path.dirname(__file__))

# Try multiple possible locations for README.md
readme_paths = [
    os.path.join(this_directory, '..', 'README.md'),  # One level up
    os.path.join(this_directory, '..', '..', 'README.md'),  # Two levels up
    os.path.join(this_directory, 'README.md'),  # Same directory
]

long_description = "A YouTube downloader app with GUI"  # Fallback description

for readme_path in readme_paths:
    if os.path.exists(readme_path):
        try:
            with open(readme_path, encoding='utf-8') as f:
                long_description = f.read()
            break
        except Exception:
            continue

# Try to read LICENSE file
license_content = "MIT"
license_paths = [
    os.path.join(this_directory, 'LICENSE'),
    os.path.join(this_directory, '..', 'LICENSE'),
]

for license_path in license_paths:
    if os.path.exists(license_path):
        try:
            with open(license_path, encoding='utf-8') as f:
                license_content = f.read()
            break
        except Exception:
            continue

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
    py_modules=["HwYtVidGrabber"],
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
            "hwytvidgrabber=HwYtVidGrabber:main",
        ],
        "gui_scripts": [
            "hwytvidgrabber-gui=HwYtVidGrabber:main",
        ],
    },
    include_package_data=True,
    package_data={
        "HwYtVidGrabber": ["*.png", "*.ico"],
    },
    project_urls={
        "Bug Reports": "https://github.com/MalikHw/HwYtVidGrabber/issues",
        "Source": "https://github.com/MalikHw/HwYtVidGrabber",
        "Funding": "https://www.ko-fi.com/MalikHw47",
    },
)
