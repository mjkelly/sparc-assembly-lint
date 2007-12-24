# -----------------------------------------------------------------
# ast.py -- Abstract syntax tree for asmlint.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
# Copyright 2007 David Lindquist (DavidEzek@gmail.com)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Thu Nov 15 17:50:04 PST 2007
# -----------------------------------------------------------------

import pprint
import copy


class Node(object):
	'''Common methods for all AST nodes. All AST classes should inherit from this.'''
	def __init__(self, *children, **keywords):
		'''Create a node with children.  Store the line number'''
		self.children = list(children)
		self.lineno = Node._getLineNumber(keywords, self.__class__.__name__)

	@staticmethod
	def _getLineNumber(hash, className):
		if hash.has_key('lineno'):
			return hash['lineno']
		else:
			raise RuntimeError(
				"[Internal Error] Keyword 'lineno' not defined for %s" % className)
	
        def getLine(self):
                return self.lineno
	
	def reduce(self):
		self.children = map(lambda x : x.reduce(), self.children)
		return self
	
	def __getitem__(self, key):
		if isinstance(key, slice):
			return self.children.__getitem__(key)
		return self.children[key]
	
        def __str__(self):
		strlist = map(str, self.children)
                return "<%s:%s>" % (self.__class__.__name__, ':'.join(strlist))

	def __repr__(self):
		'''pprint uses __repr__, not __str__, so make them the same.'''
		return self.__str__()

class File(Node):
	def __init__(self, *children, **keywords):
		Node.__init__(self, *children, **keywords)
		self.parent = None

		for (index,child) in enumerate(self.children):
			if not isinstance(child, Node):
				raise RuntimeError("Bad child list in File node: %s" % child)

			child.parent = self
			if index + 1 < len(self.children):
				child.next = self.children[index + 1]
			else:
				child.next = None

			if index != 0:
				child.prev = self.children[index - 1]
			else:
				child.prev = None

	
		def makeParentPointers(node):
			for (index,child) in enumerate(node.children):
				if not isinstance(child, Node):
					raise RuntimeError("Bad child list in node %s. Child is: %s" % (node, child))

				child.parent = node
				makeParentPointers(child)

		makeParentPointers(self)
	
	def reduce(self):
		cp = copy.deepcopy(self)
		return Node.reduce(cp)


class MacroDeclaration(Node):
	def __init__(self, name, value, **keywords):
		'''New Macro, "name=value".
		@param name Id object containing the name of the macro.
		@param value the value of the macro. Can be any type that has a resolve() method.'''
		Node.__init__(self, name, value, **keywords)
		self.name = name
		self.value = value

	def reduce(self):
		self.value = self.value.reduce()
		return self

	def __str__(self):
		return "<%s:%s=%s>" % (self.__class__.__name__, self.name, self.value)

class SingletonContainer(Node):
	def __init__(self, value, **keywords):
		Node.__init__(self, **keywords)
		self.value = value
	
	def __str__(self):
		return "<%s:%s>" % (self.__class__.__name__, self.value)

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
	def reduce(self):
		node = self

		while True:
			if not hasattr(node, 'parent'):
				raise RuntimeError("Node %s has no parent pointer! Baaad mojo!" % node)
			if isinstance(node.parent, File):
				break
			node = node.parent

		while not(node.prev is None):
			node = node.prev
			if isinstance(node, MacroDeclaration):
				if node.name.getName() == self.getName():
					return node.reduce().value
		return self

class Integer(ValueContainer):
	def __init__(self, value, **keywords):
		if isinstance(value, str):
			# base=0 auto-detects base
			ValueContainer.__init__(self, int(value, 0), **keywords)
		else:
			ValueContainer.__init__(self, value, **keywords)
	pass

class Char(ValueContainer):
	pass

class Float(ValueContainer):
	pass

class String(ValueContainer):
	pass

class Type(ValueContainer):
	pass

class Comment(Node):
	def __init__(self, *children, **keywords):
		Node.__init__(self, **keywords)
		self.text = list(children)

class BinaryExpression(Node):
	def __init__(self, name, left, right, lineno=0):
		Node.__init__(self, left, right, lineno=lineno)
		self.__class__.__name__ = name
	
	def reduce(self):
		left  = self.children[0].reduce()
		right = self.children[1].reduce()

		if isinstance(left, ValueContainer) and isinstance(right, ValueContainer):
			return Integer(self.op(left.getValue(), right.getValue()), lineno=self.lineno)
		else:
			return self
	
	def op(self, left, right):
		raise RuntimeError("Unimplemented binary operator: %s" % self.__class__.__name__)

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
	def op(self, left, right):
		return left + right

class BinaryMinus(BinaryExpression):
	def op(self, left, right):
		return left - right

class BinaryMul(BinaryExpression):
	def op(self, left, right):
		return left * right

class BinaryDiv(BinaryExpression):
	def op(self, left, right):
		return left / right

class BinaryMod(BinaryExpression):
	def op(self, left, right):
		return left % right

class BinaryXor(BinaryExpression):
	def op(self, left, right):
		return left ^ right

class BinaryLShift(BinaryExpression):
	def op(self, left, right):
		return left << right

class BinaryRShift(BinaryExpression):
	def op(self, left, right):
		return left >> right

class BinaryAnd(BinaryExpression):
	def op(self, left, right):
		return left & right

class BinaryOr(BinaryExpression):
	def op(self, left, right):
		return left | right

class UnaryExpression(Node):
	def __init__(self, name, arg, lineno=0):
		Node.__init__(self, arg, lineno=lineno)
		self.__class__.__name__ = str(name)
		self.name = name
		self.arg = arg

	def reduce(self):
		arg  = self.arg.reduce()

		if isinstance(arg, ValueContainer):
			return Integer(self.op(arg.getValue()), lineno=self.lineno)
		else:
			return self

	def op(self, arg):
		raise RuntimeError("Unimplemented unary operator: %s" % self.__class__.__name__)

	def from_str(name, arg, lineno=0):
		classes = {
			'-': UnaryMinus,
			'~': UnaryNot,
			'%lo': UnaryLo,
			'%hi': UnaryHi,
			'%r_disp32' : UnaryNop,
			'%r_plt32' : UnaryNop,
		}
		return (classes[name])(name, arg, lineno=lineno)
	
	from_str = staticmethod(from_str)

class UnaryMinus(UnaryExpression):
	def op(self, arg):
		return -arg

class UnaryNot(UnaryExpression):
	def op(self, arg):
		return ~arg

class UnaryHi(UnaryExpression):
	def op(self, arg):
		# yes, this mask is necessary: otherwise python does a signed shift
		return (arg & 0xfffffc00) >> 10

class UnaryLo(UnaryExpression):
	def op(self, arg):
		return arg & 0x000003ff

class UnaryNop(UnaryExpression):
	'''Operators that exist solely to issue warnings. %r_disp32 and
	   %r_plt32, I'm looking at you.'''
	def op(self, arg):
		return arg

class Save(Node):
	pass

class Branch(Node):
	pass

class AnnulledBranch(Node):
	pass

class Address(Node):
	def __init__(self, base, *children, **keywords):
		Node.__init__(self, **keywords)
		self.base = base
		if len(children) == 2:
			self.op = children[0]
			self.offset = children[1]
		else:
			self.op = None
			self.offset = None

	def __str__(self):
		if self.offset:
			return "<%s=%s%s%s>" % (self.__class__.__name__, self.base, self.op, self.offset)
		else:
			return "<%s=%s>" % (self.__class__.__name__, self.base)

class Instruction(Node):
	def __init__(self, name, *children, **keywords):
		Node.__init__(self, *children, **keywords)
		self.name = name

	def __str__(self):
		strlist = map(str, self.children)
		return "<%s=%s:%s>" % (self.__class__.__name__, self.name, ':'.join(strlist))

