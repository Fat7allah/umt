from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in umt/__init__.py
from umt import __version__ as version

setup(
    name="umt",
    version=version,
    description="UNEM Management Tool",
    author="UMT",
    author_email="admin@unem.ma",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
