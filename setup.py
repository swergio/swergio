import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="swergio",
    version="0.0.2",
    author="Ishmagurca",
    # author_email="author@example.com",
    description="Swergio Package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/swergio/swergio",
    #project_urls={
    #    "Bug Tracker": "https://github.com/pypa/sampleproject/issues",
    #},
    classifiers=[
        "Programming Language :: Python :: 3",
        #"License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    extras_require={
        "toolbox": ["swergio_toolbox"],
    },
)
