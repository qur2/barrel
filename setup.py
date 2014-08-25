"""Model-like encapsulation of big dict structure (like JSON data)."""
from setuptools import setup, find_packages


setup(
    name='barrel',
    version='0.1.3',
    description='python interface to reaktor API',
    long_description=__doc__,
    license='BSD',
    author='txtr web team',
    author_email='web-dev@txtr.com',
    url='https://github.com/txtr/barrel/',
    packages=find_packages(),
    platforms='any',
    install_requires=['blinker', 'iso8601', 'holon', ],
    dependency_links=[
        'https://github.com/txtr/holon/zipball/0.0.5#egg=holon',
    ]
)
