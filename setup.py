from setuptools import setup, find_packages

setup(
    name="docstool",
    version="1.0.0",
    author="Er-Akash0053",
    author_email="akashkarale0053@gmail.com",
    description="Technical Documentation Linter, Automation CLI, and SQL Audit Engine",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pyyaml>=6.0",
        "rich>=13.0"
    ],
    entry_points={
        "console_scripts": [
            "docstool=docstool.cli:main",
        ],
    },
)
