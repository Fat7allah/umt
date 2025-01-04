from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="umt",
    version="1.0.0",
    description="UNEM Management Tool",
    author="UMT",
    author_email="admin@unem.ma",
    packages=find_packages(where="."),
    package_dir={"": "."},
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
