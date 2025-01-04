from setuptools import setup, find_packages

setup(
    name='umt',
    version='1.0.0',
    description='UNEM Management Tool',
    author='UMT',
    author_email='admin@unem.ma',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'frappe>=14.0.0',
        'python-dateutil',
        'babel',
        'num2words'
    ]
)
