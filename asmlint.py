#!/usr/bin/python
# -----------------------------------------------------------------
# asmlint.py -- Find common errors in SPARC assembly files.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
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

parse_tree = []

def run(handle, opts):
	'''Run the linter on a file handle.
	@return the number of errors that occurred in the parse'''
	lineno = 0
	init_parser(opts)

	try:
		subtree = yacc.parse(handle.read(), tracking=True)
	except (ParseError, FormatCheckError), e:
		print 'Error on line %d: %s' % (lineno, e)
		other_error()

	parse_tree.append(subtree)

	# re-read file checking line lengths.  We should figure out how to do
	# this in the parser.
	handle.seek(0)
	for lineno, line in enumerate(handle):
		lineno = lineno + 1	# enumerate is 0 based
		if opts.check_line_length and len(line.rstrip('\n')) > opts.max_line_length:
			warn("%s:%d exceeds %d chars." % (handle.name, lineno, opts.max_line_length))

	return get_num_errors()

def main(argv):

	opt_parser = OptionParser(usage="%prog [OPTIONS] [FILENAME]")

	add_bool_option(opt_parser, 'check-line-length', 'check_line_length',
		true_desc="Check line length.",
		false_desc="Don't check line length. (Default)")

	opt_parser.add_option("--max-line-length", action="store", dest="max_line_length",
		type="int", help="Maximum acceptable line length when --check-line-length is on.")

	add_bool_option(opt_parser, 'check-registers', 'check_regs',
		true_desc="Check for suspicious register names. (Default)",
		false_desc="Don't check for suspicious register names.")

	opt_parser.add_option("--verbosity", action="store", dest="verbosity",
		type="int", help="Output verbosity: -1 = completely silent, 0 = quiet, 1 = some debug, 2 = copious debug. [ default: %default ]")

	opt_parser.set_defaults(max_line_length=80)
	opt_parser.set_defaults(check_line_length=False)
	opt_parser.set_defaults(check_regs=True)
	opt_parser.set_defaults(verbosity=1)

	input_file = sys.stdin

	(opts, args) = opt_parser.parse_args()

	if len(args) > 1:
		opt_parser.print_help()
		sys.exit(2)
	elif len(args) > 0:
		input_filename = args[0]
		input_file = open(input_filename, 'r')
	
	num_errors = run(input_file, opts)

	if input_file != sys.stdin:
		input_file.close()
	
	pp = pprint.PrettyPrinter(indent=2)
	if opts.verbosity >= 0:
		info("-----------------------------------------------------------------------------")
		print "FINAL PARSE TREE:"
		pp = pprint.PrettyPrinter(indent=2)
		pp.pprint(parse_tree)
		info("-----------------------------------------------------------------------------")
		print "SYMBOL TABLE:"
		print "Labels:"
		pp.pprint(ast.Label.all_labels)
		print "Macros:"
		#pp.pprint(ast.Macro.all_macros)
		for name in ast.Macro.all_macros:
			m = ast.Macro.all_macros[name]
			print "%s = %s" % (m, m.resolve())

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

def add_bool_option(parser, opt_flag_name, opt_var_name, true_desc, false_desc):
	'''optparse provides no easy way to handle full boolean flags, so here it is.'''
	parser.add_option(  '--' + opt_flag_name, action="store_true",  dest=opt_var_name, help=true_desc)
	parser.add_option('--no-' + opt_flag_name, action="store_false", dest=opt_var_name, help=false_desc)

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

if __name__ == '__main__':
	sys.exit(main(sys.argv))

