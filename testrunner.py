#!/usr/bin/python
# -----------------------------------------------------------------
# testrunner.py -- Run all unit tests.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Sun Aug 12 03:24:12 PDT 2007
# -----------------------------------------------------------------

import sys
from optparse import OptionParser, OptionGroup
import unittest

from tests.testregexes import TestRegexes
from tests.testlines import TestSingleLines
#from tests.unit_tests import UnitTests

def main():
	opt_parser = OptionParser(usage="%prog [OPTIONS]")

	opt_parser.add_option("--verbosity", action="store", dest="verbosity",
		type="int", help="Output verbosity: -1 = completely silent, 0 = quiet, 1 = some debug, 2 = copious debug.")
	opt_parser.add_option("-t", "--test", action="append", dest="run_tests",
		type="string", help="Name of specific test to run. May be given multiple times to run more than one test.")
	opt_parser.add_option("-l", "--list", action="store_true", dest="list",
		default=False, help="List names of possible tests to run with --test.")

	opt_parser.set_defaults(verbosity=-1)
	opt_parser.set_defaults(run_tests=[])

	(opts, args) = opt_parser.parse_args()

	test_runner = TestRunner(opts)

	was_successful = True

	avail_tests = []
	test_methods = {}
	for method_name in dir(test_runner):
		method = getattr(test_runner, method_name)
		if method_name.startswith('runtest_') and callable(method):
			avail_tests.append(strip_prefix('runtest_',method_name))
			test_methods[method_name] = method
	
	if opts.list:
		print "Registered tests:"
		for test in avail_tests:
			print "\t" + test
		return 0
	
	if len(opts.run_tests) != 0:
		run_tests = opts.run_tests
	else:
		run_tests = avail_tests
	
	for test in run_tests:
		method_name = 'runtest_' + test
		if not(method_name in test_methods):
			print '*** No test "%s" exists! ***' % test
			continue
		method = test_methods[method_name]
		print method_name
		ret = method()
		if not ret.wasSuccessful():
			was_successful = False
	
	if was_successful:
		return 0
	else:
		print "----------------------------------------------------------------"
		print "SOME TESTS FAILED!"
		return 1
	
def strip_prefix(prefix, str):
	'''If str begins with prefix, return str with first instance of prefix removed.'''
	if str.startswith(prefix):
		return str[len(prefix):]
	else:
		return str

class TestRunner:
	'''Contains short methods to kick off each test suite. Any method
	starting with 'runtest_NAME' is assumed to control the test suite
	NAME.'''

	def __init__(self, opts):
		self.opts = opts

	def runtest_regexes(self):
		TestRegexes.verbosity = self.opts.verbosity
		suite = unittest.TestLoader().loadTestsFromTestCase(TestRegexes)
		return unittest.TextTestRunner(verbosity=2).run(suite)

	def runtest_lines(self):
		TestSingleLines.verbosity = self.opts.verbosity
		suite = unittest.TestLoader().loadTestsFromTestCase(TestSingleLines)
		return unittest.TextTestRunner(verbosity=2).run(suite)
	
if __name__ == '__main__':
	sys.exit(main())

