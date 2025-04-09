from setuptools import setup, find_packages

setup(
    name="rollama",
    version="0.1.0",
    description="Ollama with remote capabilities",
    author="Developer",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pillow>=9.0.0",  # Added for GUI image support
    ],
    entry_points={
        "console_scripts": [
            "rollama=rollama.cli:main",
            "rollama-gui=rollama.gui:main",  # Added GUI entry point
            "rollama-code=rollama.code_cli:main",  # Added Code management entry point
        ],
    },
)
