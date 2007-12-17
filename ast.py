# -----------------------------------------------------------------
# ast.py -- Abstract syntax tree for asmlint.
# Copyright 2007 Michael Kelly, David Lindquist
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
	
	def reduce(self):
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

	
		def makePointers(node):
			for (index,child) in enumerate(node.children):
				if not isinstance(child, Node):
					continue

				child.parent = node
				if index + 1 < len(node.children):
					if not isinstance(node, File):
						child.next = node.parent.next
					else:
						child.next = node.children[index + 1]
				else:
					child.next = None

				if index != 0:
					if not isinstance(node, File):
						child.prev = node.parent.prev
					else:
						child.prev = node.children[index - 1]
				else:
					child.prev = None

			for child in node.children:
				if isinstance(child, Node):
					makePointers(child)

		makePointers(self)


class MacroDeclaration(Node):
	def __init__(self, name, value, **keywords):
		'''New Macro, "name=value".
		@param name Id object containing the name of the macro.
		@param value the value of the macro. Can be any type that has a resolve() method.'''
		Node.__init__(self, name, value, **keywords)
		self.name = name
		self.value = value

	def reduce(self):
		return MacroDeclaration(self.name, self.value.reduce(), lineno=self.lineno)

	def __str__(self):
		return "<%s:%s=%s>" % (self.__class__.__name__, self.name, self.value)

class SingletonContainer(Node):
	def __init__(self, value, **keywords):
		Node.__init__(self, value, **keywords)
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
		while node.prev != None:
			node = node.prev
			if isinstance(node, MacroDeclaration):
				if node.name == self.getName():
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

class Comment(Node):
	pass

class BinaryExpression(Node):
	def __init__(self, name, left, right, lineno=0):
		Node.__init__(self, left, right, lineno=lineno)
		self.__class__.__name__ = name
	
	def reduce(self):
		left  = self.children[0].reduce()
		right = self.children[1].reduce()

		if isinstance(left, ValueContainer) and isinstance(right, ValueContainer):
			op = self.__class__.__name__
			val = eval(str(left.value) + str(op) + str(right.value))	# blatant cheating
			return Integer(val, lineno=self.lineno)
		return self

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

	def reduce(self):
		arg  = self.children[0].reduce()

		if isinstance(arg, ValueContainer):
			op = self.__class__.__name__
			val = eval(str(op) + str(arg.value))	# blatant cheating
			return Integer(val, lineno=self.lineno)
		return self


	def from_str(name, arg, lineno=0):
		classes = {
			'-': UnaryMinus,
			'~': UnaryNot,
			'%lo': UnaryLo,
			'%hi': UnaryHi,
		}
		return (classes[name])(name, arg, lineno=lineno)
	
	from_str = staticmethod(from_str)

class UnaryMinus(UnaryExpression):
	pass

class UnaryNot(UnaryExpression):
	pass

class UnaryHi(UnaryExpression):
	pass

class UnaryLo(UnaryExpression):
	pass

class Save(Node):
	pass

class Branch(Node):
	pass

class AnnulledBranch(Node):
	pass

class Instruction(Node):
	pass
