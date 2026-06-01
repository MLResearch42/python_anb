#!/usr/bin/env python
"""Compatibility shim. Project metadata now lives in ``pyproject.toml``.

Prefer ``pip install .`` over ``python setup.py install``.
"""
from setuptools import setup

setup()
