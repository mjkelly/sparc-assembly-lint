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

import re
import unittest

class TestRegexes(unittest.TestCase):
	"""Test the non-trivial regexes"""

	def _regex_tester(self, regex, matches, nonmatches):
		"""Test a given regex against a series of positive matches and
		non-matches."""
		print "\nRegex tester:"
		r = re.compile('^' + regex + '$')

		for good in matches:
			print '\tTesting POSITIVE match: %s' % good
			self.assert_(r.match(good))

		for bad in nonmatches:
			print '\tTesting NEGATIVE match: %s' % bad
			self.assert_(not r.match(bad))
	
	def testInteger(self):
		pos = ['1', '123', '0', '05', '-1']
		neg = ['', 'foo', '1.0', '1.', '.5', '.']
		self._regex_tester(asmlint.int_regex, pos, neg)

	def testIdentifier(self):
		pos = ['foo', 'foo_bar', 'FOO', 'foo_123', '.foo', '.f1o2o3']
		neg = ['', '1foo', 'foo.bar', '', 'foo.', '.']
		self._regex_tester(asmlint.identifier_regex, pos, neg)

	def testString(self):
		pos = [r'""', r'" "', r'"foo"', r'"foo\'bar"', r'"\n"',
			r'"foo\r\nbar"', r'"\""', r'"foo\"bar"', r'"foo\\\"bar"', r'"\\"', r'"\\\""']
		neg = [r'"', r'"\'', r'"\"', r'"\\\"']
		self._regex_tester(asmlint.string_regex, pos, neg)

	def testChar(self):
		pos = [r"'c'", r"' '", r"'\n'", r"'\''", r"'\\'", "'\"'"]
		neg = [r"''", r"'\'"]
		self._regex_tester(asmlint.char_regex, pos, neg)
	
	def testFloatingPoint(self):
		pos = ['1', '1.', '1.5', '42.14159', '.5', '-.5', '0.5',
			'01.5', '1.5E4', '1e5', '0', '-0', '-1.5', '-1.5e3',
			'-1.5e-3']
		neg = ['', 'foo', '.', 'e5', '1..5', '--5', '-5e--5']
		self._regex_tester(asmlint.float_regex, pos, neg)
			
if __name__ == '__main__':
	unittest.main()
