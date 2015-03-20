#!/usr/bin/env python3

from distutils.core import setup
setup(name='pscad',
	version='0.1',
	description='Terminal based OpenSCAD file editor',
	author='Yuri Schaeffer',
	author_email='yuri@schaeffer.tk',
	url='https://github.com/yschaeff/pscad',
	
	py_modules=['clipboard', 'Datastruct', 'importer', 'undo', 'validation'],
	scripts=['pscad'],
	classifiers = [
	  "Programming Language :: Python :: 3 :: only",
	],
	requires = ["urwid", "copy", "re", "os", "collections"],
)
