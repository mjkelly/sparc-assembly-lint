#!/usr/bin/python
# -----------------------------------------------------------------
# asmlint.py -- Find common errors in SPARC assembly files.
# Copyright 2007 Michael Kelly, David Lindquist
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

from asm_parser import yacc, debug, warn, info, get_num_errors, \
	get_num_warnings, init_parser, other_error, \
	ParseError, FormatCheckError
import ast

lastResult = None

class ParseResult(object):
	def __init__(self, parse_tree, num_errors):
		self.parse_tree = parse_tree
		self.num_errors = num_errors

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

def run(handle, opts):
	'''Run the linter on a file handle.
	@return the number of errors that occurred in the parse'''
	lineno = 0
	init_parser(opts)

	parse_tree = None

	input = handle.read()
	if not input:
		warn('Empty input')
		input = ' '
	try:
		parse_tree = yacc.parse(input, tracking=True)
	except (ParseError, FormatCheckError), e:
		print 'Error on line %d: %s' % (lineno, e)
		other_error()
	
	global lastResult
	lastResult = ParseResult(parse_tree, get_num_errors())
	return lastResult
	
def main(argv):

	opt_parser = ALOptionParser(usage="%prog [OPTIONS] [FILENAME]")

	opt_parser.add_bool_option('check-registers', dest='check_regs',
		help_true="Check for suspicious register names. (Default)",
		help_false="Don't check for suspicious register names.")

	opt_parser.add_option('-v', '--verbose', action="count", dest="verbosity", 
		help="Increase verbosity of output.  Use multiple times to increase verbosity further.")
	opt_parser.add_option('-q', '--quiet', action="store_true", dest="quiet", 
		help="Silence output.")

	opt_parser.set_defaults(check_regs=True)
	opt_parser.set_defaults(verbosity=0)

	input_file = sys.stdin

	(opts, args) = opt_parser.parse_args()

	if opts.quiet:
		opts.verbosity = -1

	if len(args) > 1:
		opt_parser.print_help()
		sys.exit(2)
	elif len(args) > 0:
		input_filename = args[0]
		input_file = open(input_filename, 'r')
	
	result = run(input_file, opts)

	num_errors = result.num_errors
	parse_tree = result.parse_tree

	if input_file != sys.stdin:
		input_file.close()
	
	pp = pprint.PrettyPrinter(indent=2)
	if opts.verbosity >= 0:
		info("-----------------------------------------------------------------------------")
		print "FINAL PARSE TREE:"
		pp = pprint.PrettyPrinter(indent=2)
		pp.pprint(parse_tree)
		info("-----------------------------------------------------------------------------")

	if num_errors > 0:
		info("%d errors." % num_errors)

	num_warnings = get_num_warnings()
	if num_warnings > 0:
		info("%d warnings." % num_warnings)

	if num_errors == 0:
		return 0
	else:
		return 1

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

if __name__ == '__main__':
	sys.exit(main(sys.argv))

