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
	def __init__(self, value):
		#print "NEW Id"
		self.value = value
	def __str__(self):
		return "<Id:%s>" % self.value
	def resolve(self):
		#print "Resolving ID %s" % self
		if self.value in Macro.all_macros:
			r = Macro.all_macros[self.value].resolve()
			if isinstance(r, ASTElement):
				return self
			else:
				return r
		else:
			#print "Macro %s not found." % self.value
			return self



class Macro(ASTElement):
	# Keep track of all macros by name.
	all_macros = {}

	def __init__(self, name, value):
		'''New Macro, "name=value".
		@param name Id object containing the name of the macro.
		@param value the value of the macro. Can be any type that has a resolve() method.'''
		#print "NEW Macro"
		self.name = name.value
		self.value = value

		# try to resolve anything that's not an int
		self.value = self.value.resolve()

		Macro.all_macros[self.name] = self
		#print "MACRO: %s = %s" % (self.name, self.value)

	def __str__(self):
		return "<Macro:%s=%s>" % (self.name, self.value)
	
	def resolve(self):
		if isinstance(self.value, ASTElement):
			return self.value.resolve()
		else:
			return self.value
	
class IntExpr(ASTElement):
	def __init__(self, left, op=None, right=None, sym=False):
		#print "NEW IntExpr"
		self.left = left
		self.op = op
		self.right = right

		# if we're initialized with only one argument (which means a
		# literal)
		if (self.op is None) and (self.left is not None):
			# if it's not a symbol, it must be a literal integer
			if not sym:
				self.left = int(self.left, 0)
			# otherwise, interpret it as a symbol
			else:
				# we can only resolve things that have been
				# defined. othewise we leave it as an Id object
				# for later resolution.
				self.left = self.left.resolve()

	def __str__(self):
		if self.right is not None:
			return "(%s %s %s)" % (self.left, self.op, self.right)
		elif self.op is not None:
			return "(%s %s)" % (self.op, self.left)
		else:
			return "%s" % self.left
	
	def resolve(self):
		#print "Resolving IntExpr %s OP %s" % (self.left, self.right)
		# binary operator
		if self.right is not None:
			#print "Resolving binary operator:"
			r = self.op.resolve(self.left, self.right)
			if isinstance(r, ASTElement):
				return self
			else:
				return r
		# unary operator
		elif self.op is not None:
			#print "Resolving unary operator:"
			r = self.op.resolve(self.left)
			if isinstance(r, ASTElement):
				return self
			else:
				return r
		# literal value
		else:
			# symbols (Id objects) must be resolved
			if isinstance(self.left, ASTElement):
				return self.left.resolve()
			# other things are just literal integers
			else:
				return self.left


class BinaryOperator(ASTElement):
	def __init__(self):
		pass

	def __str__(self):
		return "<UnknownBinOp>"

	def resolve(self, left, right):
		# try to resolve each side first
		l, r = left, right
		if isinstance(left, ASTElement):
			l = left.resolve()
		if isinstance(right, ASTElement):
			r = right.resolve()
		
		# check if either resolution failed
		if isinstance(l, ASTElement) or isinstance(r, ASTElement):
			return self
		else:
			return self._do_resolve(l, r)
	
	def from_str(str):
		classes = {
			'+': Plus,
			'-': Minus,
			'*': Mul,
			'/': Div,
			'%': Mod,
			'^': Xor,
			'<<': LShift,
			'>>': RShift,
			'&': And,
			'|': Or,
		}
		return (classes[str])()
	
	from_str = staticmethod(from_str)
	
class Plus(BinaryOperator):
	def __str__(self):
		return "+"

	def _do_resolve(self, left, right):
		return left + right

class Minus(BinaryOperator):
	def __str__(self):
		return "-"

	def _do_resolve(self, left, right):
		return left - right

class Mul(BinaryOperator):
	def __str__(self):
		return "*"

	def _do_resolve(self, left, right):
		return left * right

class Div(BinaryOperator):
	def __str__(self):
		return "/"

	def _do_resolve(self, left, right):
		return left / right

class Mod(BinaryOperator):
	def __str__(self):
		return "%"

	def _do_resolve(self, left, right):
		return left % right

class Xor(BinaryOperator):
	def __str__(self):
		return "^"

	def _do_resolve(self, left, right):
		return left ^ right

class LShift(BinaryOperator):
	def __str__(self):
		return "<<"

	def _do_resolve(self, left, right):
		return left << right

class RShift(BinaryOperator):
	def __str__(self):
		return ">>"

	def _do_resolve(self, left, right):
		return left >> right

class And(BinaryOperator):
	def __str__(self):
		return "&"

	def _do_resolve(self, left, right):
		return left & right

class Or(BinaryOperator):
	def __str__(self):
		return "|"

	def _do_resolve(self, left, right):
		return left | right

class UnaryOperator(ASTElement):
	def __init__(self):
		pass

	def __str__(self):
		return "<UnknownUnaryOp>"

	def resolve(self, arg):
		# if either side can't be resolved, we can't resolve
		a = arg
		if isinstance(arg, ASTElement):
			a = arg.resolve()
		return self._do_resolve(a)
	
	def from_str(str):
		classes = {
			'-': UMinus,
			'~': Not,
		}
		return (classes[str])()
	
	from_str = staticmethod(from_str)

class UMinus(UnaryOperator):
	def __str__(self):
		return "-"

	def _do_resolve(self, arg):
		return -arg

class Not(UnaryOperator):
	def __str__(self):
		return "~"

	def _do_resolve(self, arg):
		return ~arg

