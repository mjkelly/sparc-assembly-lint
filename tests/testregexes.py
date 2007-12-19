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

import asm_parser

import re
import unittest

class TestRegexes(unittest.TestCase):
	"""Test the non-trivial regexes"""
	# If run from testrunner.py, this is overridden with testrunner's
	# value. (testrunner ALWAYS sets it.)
	verbosity = -1
	# Whether to run tests that test nonexistant or future functionality.
	run_unstable = False

	def _regex_tester(self, regex, matches, nonmatches):
		"""Test a given regex against a series of positive matches and
		non-matches."""
		if TestRegexes.verbosity >= 0:
			print "\nRegex tester:"
		r = re.compile('^' + regex + '$')

		for good in matches:
			if TestRegexes.verbosity >= 0:
				print '\tTesting POSITIVE match: %s' % good
			self.assert_(r.match(good))

		for bad in nonmatches:
			if TestRegexes.verbosity >= 0:
				print '\tTesting NEGATIVE match: %s' % bad
			self.assert_(not r.match(bad))
	
	def testInteger(self):
		pos = ['1', '123', '0', '05', '-1', '0x0', '0x123', '0xabc',
			'0xABC', '-0xff']
		neg = ['', 'foo', '1.0', '1.', '.5', '.']
		self._regex_tester(asm_parser.int_regex, pos, neg)

	def testIdentifier(self):
		pos = ['foo', 'foo_bar', 'FOO', 'foo_123', '.foo', '.f1o2o3', 'foo$bar', '$$$']
		neg = ['', '1foo']
		self._regex_tester(asm_parser.id_regex, pos, neg)
	
	def testString(self):
		pos = [r'""', r'" "', r'"foo"', r'"foo\'bar"', r'"\n"',
			r'"foo\r\nbar"', r'"\""', r'"foo\"bar"', r'"foo\\\"bar"', r'"\\"', r'"\\\""']
		neg = [r'"', r'"\'', r'"\"', r'"\\\"']
		self._regex_tester(asm_parser.string_regex, pos, neg)

	def testChar(self):
		pos = [r"'c'", r"' '", r"'\n'", r"'\''", r"'\\'", "'\"'"]
		neg = [r"''", r"'\'"]
		self._regex_tester(asm_parser.char_regex, pos, neg)
	
	def testFloatingPoint(self):
		pos = ['0r1', '0r1.', '0r1.5', '0r42.14159', '0r.5', '0r-.5', '0r0.5',
			'0r01.5', '0r1.5E4', '0r1e5', '0r0', '0r-0', '0r-1.5', '0r-1.5e3',
			'0r-1.5e-3']
		neg = ['0r', 'foo', '0rfoo', '0r.', '.', '0re5', '0r1..5',
			'0r--5', '0r-5e--5']
		self._regex_tester(asm_parser.float_regex, pos, neg)
	
	def testRegister(self):
		specials = [ '%fsr', '%fq', '%c0', '%csr', '%cq', '%psr', '%tbr', '%wim', '%y']
		unaryOperators = [ '%lo', '%hi', '%r_disp32', '%r_plt32', '%asr1' ]
		self._regex_tester(asm_parser.reg_regex, specials, unaryOperators)

		pos = []
		for i in range(0,31):
			i = str(i)
			pos.append('%r' + i)
			pos.append('%f' + i)
			pos.append('%c' + i)

		for i in range(0,7):
			i = str(i)
			pos.append('%i' + i)
			pos.append('%l' + i)
			pos.append('%o' + i)
			pos.append('%g' + i)

		neg = ['', '%%', '%', '%lO', '%l03', '%r32', '%1', '%y1', '%l8', '%r32']
		self._regex_tester(asm_parser.reg_regex, pos, neg)

if __name__ == '__main__':
	unittest.main()
