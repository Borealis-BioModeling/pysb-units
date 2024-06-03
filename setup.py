import setuptools
from setuptools import find_namespace_packages

# with open("README.md", encoding="utf8") as fh:
#     long_description = fh.read()

setuptools.setup(
    name="pysb-units",
    version="0.1.0",
    python_requires=">=3.8",
    install_requires=["pysb>=1.15.0"],
    extras_require={"cython": "cython>=0.29.25"},
    author="Blake A. Wilson",
    author_email="blakeaw1102@gmail.com",
    description="PySB add-on providing utilities to add units to models and perform dimensional analysis.",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    url="https://github.com/Borealis-BioModeling/pysb-units",
    packages=find_namespace_packages(where='src'),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)