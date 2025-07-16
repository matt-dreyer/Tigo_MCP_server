from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tigo-mcp-server",
    version="0.1.3",
    author="Matt Dreyer",
    author_email="matt_dreyer@hotmail.com",
    description="Model Context Protocol server for Tigo Energy solar system monitoring and analytics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/matt-dreyer/Tigo_MCP_server",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "python-dotenv",
        "mcp",
        "tigo-python",
    ],
    entry_points={
        "console_scripts": [
            "tigo-mcp-server=tigo_mcp_server.server:main",
        ],
    },
)