from setuptools import setup, find_packages

setup(
    name="habit-tracker",
    version="0.1.0",
    packages=find_packages(),
    package_dir={"": "src"},
    install_requires=[],
    entry_points={
        "console_scripts": [
            "habit-tracker=habit_tracker.cli:main",
        ],
    },
    python_requires=">=3.9",
)
