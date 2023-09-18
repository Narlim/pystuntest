import os.path
from setuptools import setup, find_packages

import pystuntest


def main():
    src = os.path.realpath(os.path.dirname(__file__))
    README = open(os.path.join(src, 'README.md')).read()

    setup(
        name='pystuntest',
        version=pystuntest.__version__,
        packages=find_packages(),
        zip_safe=False,
        license='MIT',
        author='Narlim',
        author_email='wangweimingooo@gmail.com',
        url='https://github.com/Narlim/pystuntest',
        description='A Python STUN client (RFC 5780)',
        long_description=README,
        keywords='STUN NAT',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.8',
            'Topic :: Internet',
            'Topic :: System :: Networking :: Firewalls',
        ],
        entry_points={
            'console_scripts': [
                'pystuntest=pystuntest.cli:main'
            ]
        }
    )

if __name__ == '__main__':
    main()