import os

from setuptools import setup, find_packages

from recommendation import VERSION


__dirname = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(__dirname, 'README.md')) as readme:
    README = readme.read()


setup(
    name='universal-search-recommendation',
    version=VERSION,
    description='Universal Search recommendation server.',
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Flask",
        "Topic :: Internet :: WWW/HTTP",
    ],
    author='Chuck Harmston',
    author_email='chuck@mozilla.com',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
