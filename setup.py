from setuptools import setup
from src import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="voiceAtis",
    version="0.0.1",
    author="Oliver Clemens",
    author_email="sowintuu@aol.com",
    description="Reads an ATIS from IVAO using voice generation.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sowintuu/voiceAtis",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Programming Language :: Python :: 2 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Microsoft :: Windows",
    ],
)
