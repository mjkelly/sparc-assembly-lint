#!/usr/bin/python
# -----------------------------------------------------------------
# section_stack.py -- Stack for sections.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
# Copyright 2007 David Lindquist (DavidEzek@gmail.com)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Thu Aug 16 01:20:52 PDT 2007
# -----------------------------------------------------------------

class SectionStack(object):
	'''Section stack object to mimic the behavior of the section stack used by the assembler.'''
	default_section = '.text'
	def __init__(self):
		'''Creates stack and puts the default section on the stack'''
		self.stack = list()
		self.push(self.default_section)

	def _getTopIndex(self):
		'''Get the array index of the top of the stack'''
		return len(self.stack) - 1

	def push(self, section):
		self.stack.append(section)

	#TODO: handle popsections on an empty stack.
	def pop(self, section):
		self.stack.pop()

	def settop(self, section):
		'''Replaces the top of the stack with section'''
		self.stack[self._getTopIndex()] = section
	
	def top(self):
		return self.stack[self._getTopIndex()]
