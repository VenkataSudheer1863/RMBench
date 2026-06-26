"""
RMBench: Benchmarking Retrieval Manipulation Attacks Against AI Agents
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rmbench",
    version="0.1.0",
    author="Venkata Sudheer Paruchuri",
    description="Benchmark for evaluating AI agent robustness against retrieval manipulation attacks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/VenkataSudheer1863/RMBench",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "scikit-learn>=1.0.0",
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "accelerate>=0.20.0",
        "sentence-transformers>=2.2.0",
        "faiss-cpu>=1.7.4",
        "datasets>=2.12.0",
        "pyyaml>=6.0",
        "tqdm>=4.65.0",
        "rich>=13.0.0",
        "requests>=2.28.0",
        "groq>=0.9.0",
        "python-dotenv>=1.0.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.12.0",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
        "notebook": [
            "jupyter>=1.0.0",
            "ipywidgets>=8.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "rmbench=benchmark.run:main",
            "rmbench-suite=benchmark.run_suite:main",
        ],
    },
)
