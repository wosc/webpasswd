"""Change a UNIX password via web UI
"""
from setuptools import setup, find_packages
import glob


setup(
    name='ws.webpasswd',
    version='2.1.0.dev0',

    install_requires=[
        'flask',
        'flask_wtf',
        'python-pam',
        'six',  # undeclared by python-pam
        'setuptools',
        'wtforms',
    ],

    extras_require={'test': [
        'pytest',
    ]},

    entry_points={
        'console_scripts': [
            'webpasswd-change = ws.webpasswd.update:main',
            'webpasswd-cgi = ws.webpasswd.web:cgi',
            'webpasswd-serve = ws.webpasswd.web:serve',
        ],
    },

    author='Wolfgang Schnerring <wosc@wosc.de>',
    author_email='wosc@wosc.de',
    license='ZPL 2.1',
    url='https://github.com/wosc/webpasswd',

    description=__doc__.strip(),
    long_description='\n\n'.join(open(name).read() for name in (
        'README.rst',
        'CHANGES.txt',
    )),

    classifiers="""\
License :: OSI Approved :: Zope Public License
Programming Language :: Python
Programming Language :: Python :: 3
"""[:-1].split('\n'),

    namespace_packages=['ws'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    data_files=[('', glob.glob('*.txt'))],
    zip_safe=False,
)
