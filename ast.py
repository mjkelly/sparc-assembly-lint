#!/usr/bin/python
# -----------------------------------------------------------------
# ast.py -- Abstract syntax tree for asmlint.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Thu Nov 15 17:50:04 PST 2007
# -----------------------------------------------------------------

import pprint

class ASTElement:
	'''Common methods for all AST elements. All AST classes should inherit from this.'''

	def __init__(self, value):
		'''The default ASTElement has only one value.'''
		self.value = value

	def __repr__(self):
		'''pprint uses __repr__, not __str__, so make them the same.'''
		return self.__str__()

class Reg(ASTElement):
	def __str__(self):
		return "<Reg:%s>" % self.value

class Label(ASTElement):
	# Keep track of all labels by name.
	all_labels = {}

	def __init__(self, id):
		'''@param id The Id object containing the label's name.'''
		self.value = id.value
		Label.all_labels[self.value] = self

	def __str__(self):
		return "<Label:%s>" % self.value

class Id(ASTElement):
	def __str__(self):
		return "<Id:%s>" % self.value

class Macro(ASTElement):
	# Keep track of all macros by name.
	all_macros = {}

	def __init__(self, name, value):
		'''New Macro, "name=value".
		@param name Id object containing the name of the macro.
		@param value the value of the macro. Varying types.'''
		self.name = name.value
		self.value = value
		Macro.all_macros[self.name] = self

	def __str__(self):
		return "<Macro:%s=...>" % self.name
