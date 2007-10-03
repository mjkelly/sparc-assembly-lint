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

import asmlint
from optparse import OptionParser, OptionGroup
import unittest

class BogusFile:
	def __init__(self, lines):
		self.lines = lines
		self.index = 0
		self.name = 'BogusFile'
		
	# Mimics readline
	def readline(self):
		# If we've reached the end of our list, return 'EOF'
		if len(self.lines) == self.index:
			return ""
		# return a line
		ret = self.lines[self.index]
		self.index += 1
		return ret

class TestSingleLines(unittest.TestCase):
	# If run from testrunner.py, this is overridden with testrunner's
	# value. (testrunner ALWAYS sets it.)
	verbosity = -1

	# Run the linter on a single line.
	# @return number of errors found
	def _runParserOneLine(self, line):
		lines = []
		lines.append(line)
		try:
			num_errors = asmlint.run(BogusFile(lines), None, None, TestSingleLines.verbosity)
		except Exception,e:
			print "ASSERT FALSE!"
			self.assert_(False)
		return num_errors

	def _runGood(self, line):
		self.assert_(self._runParserOneLine(line) == 0)

	def _runBad(self, line):
		self.assert_(self._runParserOneLine(line) != 0)

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
	
	def testLineComment(self):
		self._runGood('! line comment')
	
	def testVarAssignment(self):
		self._runGood('MYINT=10')
	
	def testVarAssignmentToHex(self):
		self._runGood('A=0x41')

	def testVarAssignmentToSymbol(self):
		self._runGood('X=label')
	
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
#	
#	def testComplexCompare(self):
#		self._runGood('cmp     %l5, NUM_OF_BANKS*4')
	
	def testSetHex(self):
		self._runGood('set     0x80000000, %l3')
	
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

	def testSkip(self):
		self._runGood('.asciz	"foo", "bar", "baz"')

	def testInvalid1(self):
		self._runBad('# foo')
	
	def testInvalid2(self):
		self._runBad('set, foo, bar')
	
	def testSave(self):
		self._runGood('save	%sp, -96, %sp')

	def testSaveExpr(self):
		self._runGood('save	%sp, -(92 + 4 + 4 + 1) & -8, %sp')

	def testBadExpr(self):
		self._runBad('save	%sp, -(92 + 2) & & -8, %sp')

	def testVarExpr(self):
		self._runGood('save	%sp, -(92 + STACK_SPACE) & -8, %sp')

			
if __name__ == '__main__':
	unittest.main()
