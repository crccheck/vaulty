from setuptools import setup


setup(
    name='vaulty',
    description='Shell interface for browsing Hashicorp Vault ',
    version='0.1.0',
    author='Chris Chang',
    author_email='c@crccheck.com',
    url='https://github.com/crccheck/vaulty',
    py_modules=['vaulty'],
    entry_points={
        'console_scripts': [
            'vaulty = vaulty:main',
        ],
    },
    install_requires=[
        'hvac',
    ],
    license='Apache License, Version 2.0',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
