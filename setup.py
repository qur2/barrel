"""Model-like encapsulation of big dict structure (like JSON data)."""
from setuptools import setup, find_packages


setup(
    name='barrel',
    version='0.0.1-dev',
    description='python interface to reaktor API',
    long_description=__doc__,
    license='BSD',
    author='txtr web team',
    author_email='web-dev@txtr.com',
    url='https://github.com/txtr/barrel/',
    packages=find_packages(),
    platforms='any',
    install_requires=['blinker', 'iso8601', 'holon==0.0.4', ],
    dependency_links=[
        'https://github.com/txtr/holon/zipball/0.0.4#egg=holon-0.0.4',
    ]
)
