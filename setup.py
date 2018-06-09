# core modules
import os
import io

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def read(file_name):
    """Read a text file and return the content as a string."""
    with io.open(os.path.join(os.path.dirname(__file__), file_name),
                 encoding='utf-8') as f:
        return f.read()

config = {
    'name': 'pysec',
    'version': '0.1.212',
    'author': 'Martin Thoma',
    'author_email': 'info@martin-thoma.de',
    'maintainer': 'Martin Thoma',
    'maintainer_email': 'info@martin-thoma.de',
    'packages': ['pysec'],
    'scripts': ['bin/pysec'],
    'package_data': {'pysec': ['templates/*', 'misc/*']},
    'platforms': ['Linux', 'MacOS X', 'Windows'],
    'url': 'https://github.com/MartinThoma/pysec',
    'license': 'MIT',
    'description': 'Tool to get stolen notebook back.',
    'long_description': read('README.md'),
    'long_description_content_type': 'text/markdown',
    'install_requires': [
        "python-networkmanager",
        "SimpleCV",
        "six"
    ],
    'keywords': ['pysec', 'security', 'notebook'],
    'download_url': 'https://github.com/MartinThoma/pysec',
    'classifiers': ['Development Status :: 7 - Inactive',
                    'Environment :: Console',
                    'Intended Audience :: Developers',
                    'License :: OSI Approved :: MIT License',
                    'Natural Language :: English',
                    'Programming Language :: Python :: 2.7',
                    'Programming Language :: Python :: 3',
                    'Programming Language :: Python :: 3.3',
                    'Programming Language :: Python :: 3.4',
                    'Topic :: Software Development',
                    'Topic :: Utilities'],
    'zip_safe': False,
    'test_suite': 'nose.collector'
}

setup(**config)
