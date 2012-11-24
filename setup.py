from os import path
from setuptools import setup

readme = ''.join(open(path.join(path.dirname(__file__), 'README.rst')))

import copipes

setup(
    name='CoPipes',
    version=copipes.__version__,
    description="A coroutine based utils for processing data via pipelines",
    long_description=readme,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='',
    author='Dmitry Vakhrushev',
    author_email='self@kr41.net',
    url='https://bitbucket.org/kr41/copipes',
    download_url='https://bitbucket.org/kr41/copipes/downloads',
    license='BSD',
    packages=['copipes'],
    include_package_data=True,
    zip_safe=True,
)
