import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="thonny-lahendus",
    # Must be exactly three numeric components: the plugin's own update check
    # (EasyExerciseProvider._get_versions) does major, minor, patch = version.split(".").
    # Only a MAJOR bump makes installed plugins prompt the user to update.
    version="10.0.1",
    author="Priit Paluoja",
    author_email="priit.paluoja@gmail.com",
    license="MIT",
    license_expression="MIT",
    description="Thonny plugin for lahendus.ut.ee",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kspar/easy-thonny",
    packages=setuptools.find_namespace_packages(),
    install_requires=[
        'easy-py>=0.8.0',
        'thonny>=4.1.4',
        'pillow>=11.3.0',
        'chevron>=0.13.1',
        'requests>=2.27.1'
    ],
    package_data={
        "thonnycontrib.easy": ["res/*.*", "templates/*.*"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    # 3.9 is the real floor: pillow>=11.3.0 requires it, and so does the Flask stack easy-py pulls in
    python_requires='>=3.9',
)
