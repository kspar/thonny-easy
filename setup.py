import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="thonny-lahendus",
    version="8.3.0",
    author="Priit Paluoja",
    author_email="priit.paluoja@gmail.com",
    license="MIT",
    description="Thonny plugin for lahendus.ut.ee",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kspar/easy-thonny",
    packages=setuptools.find_namespace_packages(),
    install_requires=[
        'easy-py>=0.7.2',
        'thonny>=4.1.4',
        'pillow>=8.0',
        'chevron>=0.13.1',
        'requests>=2.27.1'
    ],
    package_data={
        "thonnycontrib.easy": ["res/*.*", "templates/*.*"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
