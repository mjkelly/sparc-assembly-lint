#!/usr/bin/python
# -----------------------------------------------------------------
# testregexes.py
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Sun Aug 12 03:01:03 PDT 2007
# -----------------------------------------------------------------

import sys
from optparse import OptionParser, OptionGroup
from StringIO import StringIO

import asmlint
import unittest
import ast

def unstable(f):
	'''Decorator to mark a test function as unstable, which will not be run
	   unless TestSingleLines.run_unstable is true.'''
	def inner(self,*args, **kwargs):
		if self.run_unstable:
			return f(self, *args, **kwargs)
		else:
			print >> sys.stderr, "[SKIPPNG UNSTABLE TEST] ",
	return inner

class TestSingleLines(unittest.TestCase):
	# If run from testrunner.py, this is overridden with testrunner's
	# value. (testrunner ALWAYS sets it.)
	verbosity = -1
	# Whether to run tests that test nonexistant or future functionality.
	run_unstable = False

	class BogusOptions:
		'''This is a slightly ugly way of passing our custom options to
		the test parser.'''
		verbosity = None
		check_regs = True

		def __init__(self, container):
			verbosity = container.verbosity

	# Run the linter on a single line.
	# @return number of errors found
	def _runParserOneLine(self, *lines):
		try:
			input = '\n'.join(list(lines))
			result = asmlint.run(StringIO( input ), TestSingleLines.BogusOptions(self))
		except (asmlint.ParseError, asmlint.FormatCheckError), e:
			print "ASSERT FAILED!", e
			self.assert_(False)
		return result

	def _runGood(self, *lines):
		result = self._runParserOneLine(*lines)
		self.assert_(result.num_errors == 0)
		return result

	def _runBad(self, *lines):
		result = self._runParserOneLine(*lines)
		self.assert_(result.num_errors != 0)
		return result

	def testCommand(self):
		self._runGood('add     %o0, 10, %l0')
	
	def testCommand_0Args(self):
		self._runGood('ret	')
	
	def testCommand_1Args(self):
		self._runGood('clr     %l0')
	
	def testCommand_2Args(self):
		self._runGood('mov     %g0, %l0')
		self._runGood('mov     10, %l0')
		self._runGood('mov     label, %l0')
	
	def testCommand_3Args(self):
		self._runGood('add     %g0, 10, %l0')
	
	def testCommand_AndComment(self):
		self._runGood('mov	%g0, %l0! comment')
	
	def testComments(self):
		self._runGood('! line comment')
		self._runGood('/* block comment */')
	
	def testMacroAssignment(self):
		result = self._runGood('MYINT=0xA')
		macro = result.parse_tree[0]
		self.assert_(type(macro),ast.MacroDeclaration) 
		self.assert_(macro.name.value == 'MYINT') 
		integer = macro.value
		self.assert_(type(integer) == ast.Integer)
		self.assert_(integer.value == 0xA)
	
	def testMacroAssignmentToHex(self):
		self._runGood('A=0x41')

	def testMacroAssignmentToSymbol(self):
		self._runGood('X=label')

	def testMacroAssignmentReservedWord(self):
		self._runGood('mov=10')
		self._runGood('a=10')
	
	def testIntegerOperators(self):
		result = self._runGood("M1='a' + 32*3 - 128/2 >> 2")
		macro = result.parse_tree[0]
		reduced = macro.reduce()
		self.assert_(type(reduced) == ast.MacroDeclaration)
		integer = reduced.value
		self.assert_(integer.value == 32)

	def testNestedMacros(self):
		result = self._runGood('M1=5', 'M2=M1')
		macro1 = result.parse_tree[0]
		macro2 = result.parse_tree[1]
		reduced = macro2.reduce()
		self.assert_(type(reduced) == ast.MacroDeclaration)
		integer = reduced.value
		self.assert_(integer.value == 5)

	def testNestedMacroExpression(self):
		result = self._runGood('M1=5', 'M2=M1 + 5')
		macro1 = result.parse_tree[0]
		macro2 = result.parse_tree[1]
		reduced = macro2.reduce()
		self.assert_(type(reduced) == ast.MacroDeclaration)
		integer = reduced.value
		self.assert_(integer.value == 10)
	
	def testOneRegisterLoad(self):
		self._runGood('ld      [%i0], %l0')

	def testPositiveOffsetLoad(self):
		self._runGood('ld      [%i0 + 15], %l0')

	def testNegativeOffsetLoad(self):
		self._runGood('ld      [%i0 - 15], %l0')

	def testExprOffset1(self):
		self._runGood('ld      [%i0 + 15 - 2*3], %l0')

	def testExprOffset2(self):
		self._runGood('ld      [%i0 + 15 - 2*3 + MY_SPECIAL_OFFSET], %l0')

	def testTwoRegisterLoad(self):
		self._runGood('ld      [%i0 + %o0], %l0')

	def testBadBrackets(self):
		self._runBad('add     [%g0], 10, %l0')
	
	def testComplexCompare(self):
		self._runGood('cmp     %l5, NUM_OF_BANKS*4')
	
	def testSetHex(self):
		self._runGood('set     0x80000000, %l3')
		self._runGood('set     0xa, %l3')

	def testMovChar(self):
		self._runGood("mov     '*', %l3")

	def testEscapedChar(self):
		self._runGood(r"mov	'\n', %l0")
	
	def testSectionData(self):
		self._runGood('.section	".data"')
	
	def testGlobalMain(self):
		self._runGood('.global	main, foo, bar')

	# .global is a reserved word, but it should be a symbol when it appears
	# as an argument
	def testGlobalDotGlobal(self):
		self._runGood('.global	.global')

	def testSkip(self):
		self._runGood('.skip	4')
		self._runGood('.skip	4, 1')

	def testFloats(self):
		self._runGood('.single	0r4.20')
		self._runGood('.double	0r8.40')

	def testAsciz(self):
		self._runGood('.asciz	"foo", "bar", "baz"')

	def testInvalid1(self):
		self._runBad('# foo')
	
	def testInvalid2(self):
		self._runBad('set, foo, bar')

	def testInvalidWithAnnull(self):
		self._runBad('bge,a, foo')
	
	def testSave(self):
		self._runGood('save	%sp, -96, %sp')

	def testSaveExpr(self):
		self._runGood('save	%sp, -(92 + 4 + 4 + 1) & -8, %sp')

	def testBadExpr(self):
		self._runBad('save	%sp, -(92 + 2) & & -8, %sp')

	def testVarExpr(self):
		self._runGood('save	%sp, -(92 + STACK_SPACE) & -8, %sp')

	def testUnaryNegative(self):
		result = self._runGood('M1=-(90 + 2)')
		macro = result.parse_tree[0]
		reduced = macro.reduce()
		self.assert_(type(reduced) == ast.MacroDeclaration)
		integer = reduced.value
		self.assert_(integer.value == -92)


	def testCall(self):
		self._runGood('call	printf')
		self._runGood('call	printf, 3')

	def testCallStrange(self):
		self._runGood('call	printf + 8')

	def testBadCall(self):
		self._runBad('call	printf, 1, 2')

	def testBadCallAndInstruction(self):
		self._runBad('call	printf, 1, 2',
				'mov	%l1, %l2')
	
	def testBadReg1(self):
		self._runBad('add	10, %l8, %l0')
	
	def testAnnulled(self):
		self._runGood('bge,a	fooLabel')

	def testBadAnnulled(self):
		self._runBad('bge,x	fooLabel')
		self._runBad('mov,a	%l0, %l1')
	
	def testBadNumberOfArguments(self):
		self._runBad('not');
		self._runBad('mov');
		self._runBad('mov	%l0, %l1, %l2');
		self._runBad('add	%l0, %l1, %l2, %l3');
		self._runBad('bl	foo, bar');
		self._runBad('bl');
		self._runBad('bl,a');
	
	# Stuff I don't use or run into regularly, that might otherwise break
	# without me noticing. NOT floating point stuff. That deserves its own
	# category.
	def testInfrequentOps(self):
		self._runGood('not	%l0, %l1')
		self._runGood('clr	[%l0]')
		self._runGood('dec	42, %l1')
		self._runGood('.type	foo, #function')
		self._runGood('.file	"foo"')
	
	def testEmptyString(self):
		self._runGood('')


if __name__ == '__main__':
	unittest.main()
