from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="kusto-mcp",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An MCP server for Azure Kusto integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/kusto-mcp-server",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "kusto-mcp=kusto_mcp.server:main",
        ],
    },
)