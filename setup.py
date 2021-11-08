import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="fedflow",
    version="0.2.1",
    author="malanore",
    author_email="malanore.z@gmail.com",
    description="auto-scheduler for pytorch task.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/malanore-z/fedflow",
    project_urls={
        "Bug Tracker": "https://github.com/malanore-z/fedflow/issues",
    },
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    package_data={'': ['resources/*']},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.4",
    install_requires=[
        "ngpuinfo==0.1.0",
        "psutil",
        "PyYAML",
        "numpy",
        "matplotlib"
    ],
    extras_requires={
        "pytorch": [
            "torch>=1.4.0",
            "torchvision>=0.5.0"
        ]
    }

)
