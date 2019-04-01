import os
from setuptools import setup
from noisekit import __VERSION__
BASEDIR_PATH = os.path.abspath(os.path.dirname(__file__))

setup(
    name="noisekit",
#    version=open(os.path.join(BASEDIR_PATH, "VERSION"), "r").read().rstrip(),
    version=__VERSION__,
    author="Geoffrey GUERET",
    author_email="geoffrey@gueret.tech",

    description="noisekit is a noise toolkit.",
    long_description=open(os.path.join(BASEDIR_PATH, "README.md"), "r").read(),
#    long_description_content_type="text/markdown",
    url="https://github.com/ggueret/noisekit",
    license="MIT",

    packages=["noisekit"],
    python_requires=">=3.4",
    install_requires=open(os.path.join(BASEDIR_PATH, "requirements.txt"), "r").read().splitlines(),
    include_package_data=True,
#    zip_safe=False,
#    package_data={
#        "": ["VERSION", "LICENSE", "noisekit.service"]
#    },
    entry_points={
        "console_scripts": {
            "noisekit = noisekit.__main__:main",
        }
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Framework :: Pelican",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Multimedia :: Sound/Audio :: Capture/Recording",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        "Topic :: Multimedia :: Sound/Audio :: Sound Synthesis",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
