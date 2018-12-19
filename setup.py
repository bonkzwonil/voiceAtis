from setuptools import setup, find_packages
import re

# Get readme.
with open("README.md", "r") as fh:
    long_description = fh.read()

# Get version.
version = re.findall('(?<=### version )[\d\.]+(?= -)',long_description)[0]

setup(
    name="voiceAtis",
    version=version,
    author="Oliver Clemens",
    author_email="sowintuu@aol.com",
    
    description="Reads an ATIS from IVAO using voice generation.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sowintuu/voiceAtis",
    
    packages=find_packages(),
    package_data={'voiceAtis': ['*.pyc']},
#     data_files=[('voiceAtis', ['*.pyc'])],
    include_package_data=True,
    
    install_requires=[
        'pyttsx',
        'metar',
        'aviationFormula',
        ],
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Programming Language :: Python :: 2 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Microsoft :: Windows",
    ],
)