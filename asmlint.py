#!/usr/bin/python
# -----------------------------------------------------------------
# asmlint.py -- Find common errors in SPARC assembly files.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
# Copyright 2007 David Lindquist (DavidEzek@gmail.com)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Thu Aug 16 01:20:52 PDT 2007
# -----------------------------------------------------------------

from optparse import OptionParser, OptionGroup
import sys
import pprint

from asm_parser import yacc, init_parser
import ast
import treechecker

import logging


class ParseResult(object):
	def __init__(self):
		# Set number of warnings, errors
		self.num_warnings = 0
		self.num_errors   = 0

		# Create logger
		self.logger = logging.getLogger()

		class CounterHandler(logging.Handler):
			'''Increment counters in self object when messages of
			certain log levels are encountered'''
			def emit(notused, record):
				if record.levelno == logging.ERROR:
					self.num_errors += 1
				elif record.levelno == logging.WARNING:
					self.num_warnings += 1
		self.logger.addHandler(CounterHandler())

		# Attach logger functions to class
		self.debug = self.logger.debug
		self.info = self.logger.info
		self.warn = self.logger.warn
		self.error = self.logger.error
	
	def add_parse_tree(self, parse_tree):
		'''Add a produced parse tree to the result.  Performs the reduction of the parse tree.'''
		self.parse_tree = parse_tree
		if parse_tree is None:
			self.reduced_tree = None
		else:
			self.reduced_tree = parse_tree.reduce()

	def get_num_errors(self):
		return self.num_errors

	def get_num_warnings(self):
		return self.num_warnings

	def printParseTree(self):
		if self.logger.level <= logging.INFO:
			if self.logger.level == logging.DEBUG:
				print "-" * 80
				print "NON-REDUCED PARSE TREE:"
				pp = pprint.PrettyPrinter(indent=2)
				pp.pprint(self.parse_tree)

			print "-" * 80
			print "FINAL PARSE TREE:"
			pp = pprint.PrettyPrinter(indent=2)
			pp.pprint(self.reduced_tree)
			print "-" * 80
	
	def printSummary(self):
		pp = pprint.PrettyPrinter(indent=2)

		if not self.parse_tree is None:
			self.printParseTree()
	
		num_errors = self.get_num_errors()
		if num_errors > 0:
			print "%d errors." % num_errors

		num_warnings = self.get_num_warnings()
		if num_warnings > 0:
			print "%d warnings." % num_warnings
	

class ALOptionParser(OptionParser):
	'''Make it easier to add boolean options (--foo and --no-foo).'''
	def add_bool_option(self, name, dest, help_true, help_false):
		'''Add a boolean command-line option. Parameters:
			name: Command-line name of the flag.
			dest: Name of the variable to store resultant boolean in.
			help_true: Help description for true option.
			help_false: Help description for false option.'''
		self.add_option('--' + name, action="store_true",  dest=dest, help=help_true)
		self.add_option('--no-' + name, action="store_false", dest=dest, help=help_false)

def run(handle, opts, treecheckers = []):
	'''Run the linter on a file handle.
	@return the number of errors that occurred in the parse'''

	# create result to build
	result = ParseResult()
	lastResult = result

	init_parser(result)
	parse_tree = None

	input = handle.read()
	# hack to avoid an error from PLY on empty input.
	if not input:
		result.warn('Empty input')
		input = ' '

	parse_tree = yacc.parse(input, tracking=True)
	
	result.add_parse_tree(parse_tree)
	for checker in treecheckers:
		checker(result)
	return result

def setLogLevel(verbosity):
	level = logging.DEBUG
	if verbosity == 0:
		level = logging.WARNING
	elif verbosity == 1:
		level = logging.INFO
	logging.getLogger().setLevel(level)


def addConsoleLogHandler():
	handler = logging.StreamHandler()
	handler.setFormatter(
		logging.Formatter("%(levelname)s: %(message)s")
	)
	logging.getLogger().addHandler(handler)
	
def main(argv):

	opt_parser = ALOptionParser(usage="%prog [OPTIONS] [FILENAME]")

	opt_parser.add_option('-v', '--verbose', action="count", dest="verbosity", 
		help="Increase verbosity of output.  Use multiple times to increase verbosity further.")
	opt_parser.add_option('-q', '--quiet', action="store_true", dest="quiet", 
		help="Silence output.")

	opt_parser.set_defaults(verbosity=0)

	input_file = sys.stdin

	(opts, args) = opt_parser.parse_args()

	if not opts.quiet:
		addConsoleLogHandler()

	setLogLevel(opts.verbosity)

	if len(args) > 1:
		opt_parser.print_help()
		sys.exit(2)
	elif len(args) > 0:
		input_filename = args[0]
		input_file = open(input_filename, 'r')
	
	result = run(input_file, opts, treechecker.allChecks)

	if input_file != sys.stdin:
		input_file.close()
	
	result.printSummary()

	if result.get_num_errors() == 0:
		return 0
	else:
		return 1

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

if __name__ == '__main__':
	sys.exit(main(sys.argv))

