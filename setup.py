from pathlib import Path

import setuptools

long_description = Path("README.md").read_text()

setuptools.setup(
    name="ci_cd_pipeline",
    version="0.0.1",
    description="An template for AWS CDK Pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tomasz Szuster",
    package_dir={"": "cdk"},
    packages=setuptools.find_packages(where="cdk"),
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
