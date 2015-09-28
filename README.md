[![Build Status](https://travis-ci.org/txtr/barrel.svg?branch=master)](https://travis-ci.org/qur2/barrel)
[![Coverage Status](https://coveralls.io/repos/txtr/barrel/badge.png?branch=master)](https://coveralls.io/r/qur2/barrel?branch=master)

# Barrel

This library enables model-like encapsulation of big dict structure (like JSON data).

>When I die I want to decompose in a barrel of porter and have it served in all the pubs in Dublin.

_J. P. Donleavy_

The goal is to __not__ map the underlying dict but just wrap it in a programmer-friendly structure
to allow attribute-like access and field aliasing.

Field aliasing enables to virtually:

* change key names
* modify the apparent structure of the dict

## Installation

Nothing to fancy - clone the repo and run
```
python setup.py install
```
Or using pip:

```
pip install https://github.com/txtr/barrel/archive/master.zip
```

##### Requirements:

* `holon` - library that provides an interface to communicate with the [Reaktor](http://txtr.com/reaktor/api/).
* `blinker` - events dispatching library.

`python-money` might become a requirement to simplify the amount \ currency handling.
At the moment it is useless, because of the Reaktor inconsistency.

## Usage

Please, refer to tests.

## Running tests

```
python -m unittest discover barrel.tests
```

## License

BSD, see `LICENSE` for more details.

## Contributors

txtr web team - [web-dev@txtr.com](mailto:web-dev@txtr.com).
