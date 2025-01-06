from os import path
from setuptools import setup, find_packages
from mrstream.version import __version__

# Get the long description from the README file
#here = path.abspath( path.dirname( __file__ ) )
#with open( path.join( here, "DESCRIPTION.rst" ), encoding="utf-8" ) as f:
#    long_description = f.read()

setup(
    name="mrstream",
    version=__version__,
    description=(
        "The multistreaming multitool"
    ),
    license="BSD",
    author="Scott Percival",
    author_email="code@moral.net.au",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3",
    install_requires=[
        "typing_extensions",
        "requests >= 2.28.0",
        "oauth2-client >= 1.2.1",
        "appdirs >= 1.4.4",
        "twitchAPI == 4.3.1",
        "thefuzz >= 0.19.0",
        "websockets == 12.0",
    ],
    extras_require={
    },
    packages=["mrstream"],
    entry_points={
        "console_scripts": [
            "mrstream = mrstream.cli:main",
        ],
    },
)

