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
import treechecker

def unstable(f):
	'''Decorator to mark a test function as unstable, which will not be run
	   unless TestLines.run_unstable is true.'''
	def inner(self,*args, **kwargs):
		if self.run_unstable:
			return f(self, *args, **kwargs)
		else:
			print >> sys.stderr, "[SKIPPNG UNSTABLE TEST] ",
	return inner

	
class TestCode(unittest.TestCase):
	# Whether to run tests that test nonexistant or future functionality.
	run_unstable = False

	basicStart = [ 
		'.section ".text"', 
		'.global main',
		'main:',
		'save	%sp, -96, %sp',
	]
	basicEnd = [
		'ret',
		'restore'
	]

	basicFile = basicStart + basicEnd

	def runParser(self, *lines):
		'''Run the linter on the passed in lines.  Returns a result object containing the parse tree and more.'''
		input = '\n'.join(list(lines))
		result = asmlint.run(StringIO(input), object(), treechecker.allChecks)
		return result

	def _runGood(self, *lines):
		result = self.runParser(*lines)
		num_errors = result.get_num_errors()
		num_warnings = result.get_num_warnings()
		self.assert_(num_errors == 0, str(num_errors))
		self.assert_(num_warnings == 0, str(num_warnings))
		return result

	def _runBad(self, *lines):
		result = self.runParser(*lines)
		num_errors = result.get_num_errors()
		self.assert_(num_errors != 0, str(num_errors))
		return result

	def _runWarn(self, *lines):
		result = self.runParser(*lines)
		num_errors = result.get_num_errors()
		num_warnings = result.get_num_warnings()
		self.assert_(num_warnings != 0, str(num_warnings))
		self.assert_(num_errors == 0, str(num_errors))
		return result

	def _get_macro_value(self, name, parse_tree):
		for instr in parse_tree.children:
			if isinstance(instr, ast.MacroDeclaration) and instr.name.value == name:
				return instr.value.reduce()


class TestLines(TestCode):
	def runParser(self, *lines):
		'''Run the lines through the parser by inserting them inside of a main declaration'''
		code = self.basicStart + list(lines) + self.basicEnd
		return TestCode.runParser(self, *code)

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
		myint = self._get_macro_value('MYINT', result.parse_tree)
		self.assert_(type(myint) == ast.Integer)
		self.assert_(myint.value == 0xA)
	
	def testMacroAssignmentToHex(self):
		self._runGood('A=0x41')

	def testMacroAssignmentToSymbol(self):
		self._runGood('X=label')

	def testMacroAssignmentReservedWord(self):
		self._runGood('mov=10')
		self._runGood('a=10')
	
	def testIntegerOperators(self):
		result = self._runGood("M1='a' + 32*3 - 128/2 >> 2")
		m1 = self._get_macro_value('M1', result.parse_tree)
		self.assert_(m1.value == 32)

	def testNestedMacros(self):
		result = self._runGood('M1=5', 'M2=M1')
		m1 = self._get_macro_value('M1', result.parse_tree)
		m2 = self._get_macro_value('M2', result.parse_tree)
		self.assert_(m1.value == 5)
		self.assert_(m2.value == 5)

	def testNestedMacroExpression(self):
		result = self._runGood('M1=5', 'M2=M1 + 5')
		m1 = self._get_macro_value('M1', result.parse_tree)
		m2 = self._get_macro_value('M2', result.parse_tree)
		self.assert_(m1.value == 5)
		self.assert_(m2.value == 10)
	
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
	
	def testGlobalMain(self):
		self._runGood('.global	main, foo, bar')

	# .global is a reserved word, but it should be a symbol when it appears
	# as an argument
	def testGlobalDotGlobal(self):
		self._runGood('.global	.global')

	def testSkip(self):
		self._runGood('.section ".bss"', '.skip	4', '.section ".text"')
		self._runGood('.section ".bss"', '.skip	4, 1', '.section ".text"')

	def testFloats(self):
		self._runGood('.section ".data"', '.single	0r4.20', '.section ".text"')
		self._runGood('.section ".data"', '.double	0r8.40', '.section ".text"')

	def testAsciz(self):
		self._runGood('.section ".data"', '.asciz	"foo", "bar", "baz"', '.section ".text"')

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
		m1 = self._get_macro_value('M1', result.parse_tree)
		self.assert_(m1.value == -92)

	def testHi(self):
		result = self._runGood('M1=~0','M2=%hi(M1)')
		m1 = self._get_macro_value('M2', result.parse_tree)
		self.assert_(m1.value == 0x003fffff)

	def testLo(self):
		result = self._runGood('M1=%lo(0xffffffff)')
		m1 = self._get_macro_value('M1', result.parse_tree)
		self.assert_(m1.value == 0x000003ff)

	def testUnimplementedOperators(self):
		self._runGood('set	%r_disp32(0xf1f1f1f1), %l0')
		self._runGood('set	%r_plt32(0xf1f1f1f1), %l0')
		result = self._runGood('M1=%r_plt32(%r_disp32(123))')
		m1 = self._get_macro_value('M1', result.parse_tree)
		self.assert_(m1.value == 123)

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
	
	def testBadArgumentType(self):
		self._runBad('add	10, %l7, %l0')
	
	def testAnnulled(self):
		self._runGood('bge,a	fooLabel', 'nop')

	def testBadAnnulled(self):
		self._runBad('bge,x	fooLabel')
		self._runBad('mov,a	%l0, %l1')
	
	def testBadNumberOfArguments(self):
		self._runBad('not')
		self._runBad('mov')
		self._runBad('mov	%l0, %l1, %l2')
		self._runBad('add	%l0, %l1, %l2, %l3')
		self._runBad('bl	foo, bar')
		self._runBad('bl')
		self._runBad('bl,a')
	
	def testSaveOffset(self):
		self._runGood('save	%sp, -96, %sp')
		self._runGood('MACRO=-96', 'save %sp, MACRO, %sp')
		self._runGood('EXTRA_VARS=7', 'STACK_SIZE = -( 92 + EXTRA_VARS ) & -8', 'save %sp, STACK_SIZE, %sp')
		self._runWarn('save %sp, -95, %sp')
		self._runWarn('save %sp, 96, %sp')
		self._runWarn('EXTRA_VARS=7', 'STACK_SIZE = -( 92 + EXTRA_VARS ) & -7', 'save %sp, STACK_SIZE, %sp')

	def testLabelAsDelayInstruction(self):
		self._runWarn('bge,a	fooLabel', 'label:')
		self._runWarn('bge	fooLabel', 'label:')

	def testBranchAsDelayInstruction(self):
		self._runWarn('bge,a	fooLabel', 'bge,a	fooLabel', 'nop')
		self._runWarn('bl	fooLabel', 'be	fooLabel', 'nop')

	def testBranchAsDelayInstruction(self):
		self._runWarn('bge	fooLabel', 'set 0, %l0')

	def testWrongSection(self):
		'''Suspicious mnemonics for current section'''
		# switching sections before ret/restore (part of the implicit wrapper)
		self._runWarn('.section ".bss"')
		self._runWarn('.section ".data"')

		# any bss/data-only decl in text section
		self._runWarn('.ascii "foo"')
		self._runWarn('.asciz "foo"')
		self._runWarn('.byte 1')
		self._runWarn('.double 0r1.0')
		self._runWarn('.half 1')
		self._runWarn('.nword 1')
		self._runWarn('.quad 0r1.0')
		self._runWarn('.single 0r1.0')
		self._runWarn('.uahalf 1')
		self._runWarn('.uaword 1')
		self._runWarn('.word 1')
		self._runWarn('.xword 1')
		self._runWarn('.skip 1')
	
	def testMultipleSectionAttributes(self):
		'''cc(1)-style .section'''
		self._runGood('.section        ".text",#alloc,#execinstr')
	
	# Stuff I don't use or run into regularly, that might otherwise break
	# without me noticing. NOT floating point stuff. That deserves its own
	# category.
	def testInfrequentOps(self):
		self._runGood('not	%l0, %l1')
		self._runGood('clr	[%l0]')
		self._runGood('dec	42, %l1')
		self._runGood('.type	foo, #function')
		self._runGood('.file	"foo"')

	def testBranchAliases(self):
		'''Undocumented aliases beq, bgt, blt'''
		self._runGood('beq	label')
		self._runGood('bgt	label')
		self._runGood('blt	label')
	
	def testRegisterWarnings(self):
		'''Warnings on suspicious register names'''
		self._runWarn("mov	%i6, %l0")
		self._runWarn("mov	%i7, %l0")
		self._runWarn("mov	%o6, %l0")
		self._runWarn("mov	%o7, %l0")
	
class TestSingleErrorOnSyntax(TestCode):
	def runSingleError(self, *lines):
		result = self.runParser(*lines)
		num_errors = result.get_num_errors()
		num_warnings = result.get_num_warnings()
		self.assert_(num_warnings == 0, str(num_warnings))
		self.assert_(num_errors == 1, "Errors: " + str(num_errors) + "\n" + "\n".join(lines))
		return result
	
	def testBadRegister(self):
		code = self.basicStart + [ 'mov %ll, %l1', 'mov %l0, %l1' ]
		result = self.runSingleError(*code)
		
	def testBadBranch(self):
		code = self.basicStart + [ 'bge,a, foo', 'mov %l0, %l1' ]
		result = self.runSingleError(*code)

	def testBadOperand(self):
		code = self.basicStart + [ 'add 10, %l8, %l0', 'add %l1, %l1, %l0' ]
		result = self.runSingleError(*code)
	
	def testBadOperand(self):
		code = self.basicStart + [ 'not', 'add %l1, %l1, %l0' ]
		result = self.runSingleError(*code)

	def testBadOperand(self):
		code =  [ 
			'.section ".text"', 
			'.global main',
			'main:',
			'save	%sp, -(92 + 2) & & -8, %sp', 
			'add %l1, %l1, %l0' 
		]
		result = self.runSingleError(*code)


class TestFiles(TestCode):
	sectionNames = [
		'.bss', 
		'.comment', 
		'.data', 
		'.data', 
		'.debug', 
		'.fini', 
		'.init', 
		'.rodata', 
		'.rodata1', 
		'.text', 
		'.line', 
		'.note' 
	]


	def testBranchAsLastInstruction(self):
		'''Branch as last instruction'''
		instr1 = self.basicStart + [ 'bge,a fooLabel', '']
		instr2 = self.basicStart + ['mov 1, %l0', 'bge,a fooLabel']
		self._runWarn(*instr1)
		self._runWarn(*instr2)
	
	def testEmptyString(self):
		'''Parsing an empty string generates a warning'''
		self._runWarn('')

	def testGoodSections(self):
		'''All the ways to declare sections'''
		code = []
		code += self.sectionNames
		code += [ '.section "%s"' % x for x in self.sectionNames ]
		code += self.basicFile
		self._runGood(*code)

	@unstable
	def testInstructionInTextSectionOnly(self):
		'''Instructions only go in the text section'''
		code = []
		badSectionsForCode = self.sectionNames
		badSectionsForCode.remove('.text')
		code += [ '.section "%s\nmov %%g0, %%g0"' % x for x in badSectionsForCode ]
		self._runWarn(*code)


if __name__ == '__main__':
	unittest.main()
