from setuptools import setup, find_packages
import os

# Read the contents of README file
with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="notionsync",
    version="0.1.0",
    description="Sync markdown files with Notion pages, similar to git functionality",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Takuya Itabashi",
    author_email="",
    url="https://github.com/yourusername/notionsync",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "python-dotenv>=0.19.0",
        "notion-client>=1.0.0",
        "requests>=2.26.0",
        "rich>=10.0.0",
        "mistune>=2.0.0",
        "mistletoe>=0.7.0",
    ],
    entry_points={
        "console_scripts": [
            "notionsync=notionsync.cli.commands:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
) 