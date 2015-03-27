import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='Django Eventbrite',
    version='0.1.0',
    author='Steve Pomeroy',
    author_email='steve@staticfree.info',
    packages=[
        'django_eventbrite',
        'django_eventbrite.management',
        'django_eventbrite.management.commands',
        ],
    include_package_data=True,
    exclude_package_data={
        '': ['*.pyc'],
        },
    url='https://github.com/xxv/django-eventbrite',
    license='BSD LICENSE',
    description='An Eventbrite app for Django',
    long_description=README,
    install_requires=[
        "django-money >= 0.5.0",
        ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
