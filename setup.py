import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="easy-thonny",
    version="0.1.0",
    author="Priit Paluoja",
    author_email="priit.paluoja@gmail.com",
    description="Thonny plugin for lahendus.ut.ee",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kspar/easy-thonny",
    packages=setuptools.find_packages(),
    install_requires=[
        'easy>=0.0.4'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
