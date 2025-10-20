from setuptools import setup, find_packages

setup(
    name="glow",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "requests>=2.25.0",
        "pillow>=9.0.0",
        "pyyaml>=6.0",
        "openai>=1.0.0",
        "jsonschema>=4.0.0",
        "python-dotenv>=0.19.0",
        "opencv-python>=4.5.0",
        "numpy>=1.20.0",
    ],
    entry_points={
        "console_scripts": [
            "glow=glow.cli:main",
        ],
    },
    python_requires=">=3.8",
    author="Adobe Glow Team",
    author_email="ed.lee.ai@proton.me",
    description="Creative Automation Pipeline for Social Ad Campaigns",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/edlee123/glow",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)