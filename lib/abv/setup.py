from setuptools import setup, find_packages

setup(
    name="abv",
    version="0.1.0",
    author="Timothy McKenna",
    author_email="mckenna.tim@gmail.com",
    description="utilities for ABV Chorus website management",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        # No external dependencies - uses built-in ftplib
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)