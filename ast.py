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

def getLineNumber(hash, className):
	if hash.has_key('lineno'):
		return hash['lineno']
	else:
		raise RuntimeError(
			"[Internal Error] Keyword 'lineno' not defined for %s" % className)

class Node(object):
	'''Common methods for all AST nodes. All AST classes should inherit from this.'''

	def __init__(self, *children, **keywords):
		'''Create a node with children.  Store the line number'''
		self.children = list(children)
		self.lineno = getLineNumber(keywords, self.__class__.__name__)
	
        def getLine(self):
                return self.lineno
    
        def __str__(self):
		strlist = map(str, self.children)
                return "<%s:%s>" % (self.__class__.__name__, ':'.join(strlist))

	def __repr__(self):
		'''pprint uses __repr__, not __str__, so make them the same.'''
		return self.__str__()

class MacroDeclaration(object):
	def __init__(self, name, value, **keywords):
		'''New Macro, "name=value".
		@param name Id object containing the name of the macro.
		@param value the value of the macro. Can be any type that has a resolve() method.'''
		self.name = name
		self.value = value
		self.lineno = getLineNumber(keywords, self.__class__.__name__)

	def __str__(self):
		return "<%s:%s=%s>" % (self.__class__.__name__, self.name, self.value)

	def __repr__(self):
		'''pprint uses __repr__, not __str__, so make them the same.'''
		return self.__str__()

class SingletonContainer(object):
	def __init__(self, value, **keywords):
		self.value = value
		self.lineno = getLineNumber(keywords, self.__class__.__name__)

	def __str__(self):
		return "<%s:%s>" % (self.__class__.__name__, self.value)

	def __repr__(self):
		'''pprint uses __repr__, not __str__, so make them the same.'''
		return self.__str__()

class NameContainer(SingletonContainer):
	def getName(self):
		return self.value

class ValueContainer(SingletonContainer):
	def getValue(self):
		return self.value

class Reg(NameContainer):
	pass

class LabelDeclaration(NameContainer):
	pass

class Id(NameContainer):
	pass

class Integer(ValueContainer):
	def __init__(self, value, **keywords):
		base = 10
		if value.startswith('0x'):
			base = 16
		elif value.startswith('0'):
			base = 8
		ValueContainer.__init__(self, int(value, base), **keywords)
	pass

class Char(ValueContainer):
	pass

class Comment(Node):
	pass

class BinaryExpression(Node):
	def __init__(self, name, left, right, lineno=0):
		Node.__init__(self, left, right, lineno=lineno)
		self.__class__.__name__ = name

	def from_str(name, left, right, lineno=0):
		classes = {
			'+': BinaryPlus,
			'-': BinaryMinus,
			'*': BinaryMul,
			'/': BinaryDiv,
			'%': BinaryMod,
			'^': BinaryXor,
			'<<': BinaryLShift,
			'>>': BinaryRShift,
			'&': BinaryAnd,
			'|': BinaryOr,
		}
		return (classes[name])(name, left, right, lineno=lineno)
	
	from_str = staticmethod(from_str)
	
class BinaryPlus(BinaryExpression):
	pass

class BinaryMinus(BinaryExpression):
	pass

class BinaryMul(BinaryExpression):
	pass

class BinaryDiv(BinaryExpression):
	pass

class BinaryMod(BinaryExpression):
	pass

class BinaryXor(BinaryExpression):
	pass

class BinaryLShift(BinaryExpression):
	pass

class BinaryRShift(BinaryExpression):
	pass

class BinaryAnd(BinaryExpression):
	pass

class BinaryOr(BinaryExpression):
	pass

class UnaryExpression(Node):
	def __init__(self, name, arg, lineno=0):
		Node.__init__(self, arg, lineno=lineno)
		self.__class__.__name__ = str(name)

	def from_str(name, arg, lineno=0):
		classes = {
			'-': UnaryMinus,
			'~': UnaryNot,
		}
		return (classes[name])(name, arg, lineno=lineno)
	
	from_str = staticmethod(from_str)

class UnaryMinus(UnaryExpression):
	pass

class UnaryNot(UnaryExpression):
	pass

class Save(Node):
	pass

class Branch(Node):
	pass

class AnnulledBranch(Node):
	pass

class Instruction(Node):
	pass
