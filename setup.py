"""
Setup script for Autonomous Drone Navigation System
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="autonomous-drone-navigation",
    version="1.0.0",
    author="Autonomous Drone Navigation Team",
    author_email="contact@example.com",
    description="An intelligent drone navigation system using computer vision and machine learning",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/autonomous-drone-navigation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
            "myst-parser>=0.15",
        ],
    },
    entry_points={
        "console_scripts": [
            "drone-nav=src.main_window_final:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords="drone, autonomous, navigation, computer-vision, machine-learning, yolo, tello",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/autonomous-drone-navigation/issues",
        "Source": "https://github.com/yourusername/autonomous-drone-navigation",
        "Documentation": "https://github.com/yourusername/autonomous-drone-navigation/docs",
    },
) 