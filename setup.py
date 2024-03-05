"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['filters_app.py']
DATA_FILES = ['filters_data/*']
OPTIONS = {}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    resources=['mytk.py']
)
