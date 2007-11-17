#!/usr/bin/python
# -----------------------------------------------------------------------------
# symbols.py -- List of reserved words in SPARC assembly.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Wed Nov 14 20:34:57 PST 2007
# -----------------------------------------------------------------------------

# These are all special case values of the ID token -- they are split off into
# their individual types so we can parse instruction formats. They are
# recombined into the 'id' production so they aren't illegal branch  targets,
# assembler variables, etc.

# Major holes in opcode support: anything that touches coprocessor registers, traps.
reserved = {
	# annullment annotation
	'a'             :       {'type':'A'},

	# attribute names: #write, #alloc, #execinstr
	'write'         :       {'type':'ATTRNAME'},
	'alloc'         :       {'type':'ATTRNAME'},
	'execinstr'     :       {'type':'ATTRNAME'},

	'object'        :       {'type':'TYPENAME'},
	'function'      :       {'type':'TYPENAME'},
	'no_type'       :       {'type':'TYPENAME'},

	# specials
	'call'          :       {'type':'CALL'},

	# integer branches
	# http://docs.sun.com/app/docs/doc/816-1681/6m83631kj?a=view
	'bn'            :       {'type':'IBRANCH'},

	'bnz'           :       {'type':'IBRANCH'},
	'bne'           :       {'type':'IBRANCH'},

	'be'            :       {'type':'IBRANCH'},
	'bz'            :       {'type':'IBRANCH'},
	'bg'            :       {'type':'IBRANCH'},
	'ble'           :       {'type':'IBRANCH'},
	'bge'           :       {'type':'IBRANCH'},
	'bl'            :       {'type':'IBRANCH'},
	'bgu'           :       {'type':'IBRANCH'},
	'bleu'          :       {'type':'IBRANCH'},

	'bcc'           :       {'type':'IBRANCH'},
	'bgeu'          :       {'type':'IBRANCH'},

	'bcs'           :       {'type':'IBRANCH'},
	'blu'           :       {'type':'IBRANCH'},
	'bpos'          :       {'type':'IBRANCH'},
	'bneg'          :       {'type':'IBRANCH'},
	'bvc'           :       {'type':'IBRANCH'},
	'bvs'           :       {'type':'IBRANCH'},

	'ba'            :       {'type':'IBRANCH'},
	'b'             :       {'type':'IBRANCH'},

	# branch on coprocessor condition codes
	'cbn'           :       {'type':'IBRANCH'},
	'cb3'           :       {'type':'IBRANCH'},
	'cb2'           :       {'type':'IBRANCH'},
	'cb23'          :       {'type':'IBRANCH'},
	'cb1'           :       {'type':'IBRANCH'},
	'cb13'          :       {'type':'IBRANCH'},
	'cb12'          :       {'type':'IBRANCH'},
	'cb123'         :       {'type':'IBRANCH'},
	'cb0'           :       {'type':'IBRANCH'},
	'cb03'          :       {'type':'IBRANCH'},
	'cb02'          :       {'type':'IBRANCH'},
	'cb023'         :       {'type':'IBRANCH'},
	'cb01'          :       {'type':'IBRANCH'},
	'cb013'         :       {'type':'IBRANCH'},
	'cb13'          :       {'type':'IBRANCH'},
	'cba'           :       {'type':'IBRANCH'},

	# floating-point branches
	'fbn'           :       {'type':'IBRANCH'},
	'fbu'           :       {'type':'IBRANCH'},
	'fbg'           :       {'type':'IBRANCH'},
	'fbug'          :       {'type':'IBRANCH'},
	'fbl'           :       {'type':'IBRANCH'},
	'fbul'          :       {'type':'IBRANCH'},
	'fblg'          :       {'type':'IBRANCH'},

	'fbne'          :       {'type':'IBRANCH'},
	'fbe'           :       {'type':'IBRANCH'},

	'fbue'          :       {'type':'IBRANCH'},
	'fbge'          :       {'type':'IBRANCH'},
	'fbuge'         :       {'type':'IBRANCH'},
	'fble'          :       {'type':'IBRANCH'},
	'fbule'         :       {'type':'IBRANCH'},
	'fbo'           :       {'type':'IBRANCH'},
	'fba'           :       {'type':'IBRANCH'},

	# flush instruction cache
	'flush'		:	{'type':'NOARGS',},

	# jump and link
	'jmpl'		:	{'type':'ONEREG',},

	# Synthetic
	'ret'		:	{'type':'NOARGS',},
	'retl'		:	{'type':'NOARGS',},
	'nop'		:	{'type':'NOARGS',},
	'restore'       :       {'type':'RESTORE'},

	'btst'          :       {'type':'MOV'},
	'bset'          :       {'type':'MOV'},
	'bclr'          :       {'type':'MOV'},
	'btog'          :       {'type':'MOV'},

	'restore'       :       {'type':'RESTORE'},
	'restore'       :       {'type':'RESTORE'},

	'inc'		:	{'type':'REGOPTCONST',},
	'inccc'		:	{'type':'REGOPTCONST',},
	'dec'		:	{'type':'REGOPTCONST',},
	'deccc'		:	{'type':'REGOPTCONST',},
	'clr'		:	{'type':'ONEREGORADDR',},
	'clrb'		:	{'type':'ONEADDR',},
	'clrh'		:	{'type':'ONEADDR',},

	'not'           :       {'type':'ONEORTWOREG',},
	'neg'           :       {'type':'ONEORTWOREG',},
	'jmp'           :       {'type':'ONEADDR',},
	'skipz'		:	{'type':'NOARGS',},
	'skipnz'	:	{'type':'NOARGS',},
	'tst'		:	{'type':'ONEREG',},

	# two arguments; different restrictions on each
	'mov'		:	{'type':'MOV',},
	'set'		:	{'type':'SET',},
	'sethi'		:	{'type':'SET',},
	'cmp'           :       {'type':'CMP',},

	# format3 opcodes
	'add'           :       {'type':'FORMAT3',},
	'addcc'         :       {'type':'FORMAT3',},
	'addx'          :       {'type':'FORMAT3',},
	'addxcc'        :       {'type':'FORMAT3',},
	'and'           :       {'type':'FORMAT3',},
	'andcc'         :       {'type':'FORMAT3',},
	'andn'          :       {'type':'FORMAT3',},
	'save'          :       {'type':'FORMAT3',},
	'sdiv'          :       {'type':'FORMAT3',},
	'sdivcc'        :       {'type':'FORMAT3',},
	'sll'           :       {'type':'FORMAT3',},
	'smul'          :       {'type':'FORMAT3',},
	'smulcc'        :       {'type':'FORMAT3',},
	'sra'           :       {'type':'FORMAT3',},
	'srl'           :       {'type':'FORMAT3',},
	'sub'           :       {'type':'FORMAT3',},
	'subcc'         :       {'type':'FORMAT3',},
	'subx'          :       {'type':'FORMAT3',},
	'subxcc'        :       {'type':'FORMAT3',},
	'taddcc'        :       {'type':'FORMAT3',},
	'taddcctv'      :       {'type':'FORMAT3',},
	'tsubcc'        :       {'type':'FORMAT3',},
	'tsubcctv'      :       {'type':'FORMAT3',},
	'udiv'          :       {'type':'FORMAT3',},
	'udivcc'        :       {'type':'FORMAT3',},
	'umul'          :       {'type':'FORMAT3',},
	'umulcc'        :       {'type':'FORMAT3',},
	'xnor'          :       {'type':'FORMAT3',},
	'xnorcc'        :       {'type':'FORMAT3',},
	'xor'           :       {'type':'FORMAT3',},
	'xnor'          :       {'type':'FORMAT3',},
	'or'            :       {'type':'FORMAT3',},
	'orcc'          :       {'type':'FORMAT3',},
	'mulscc'        :       {'type':'FORMAT3',},

	# automatic illegal instruction!
	'unimp'         :       {'type':'NOARGS',},

	# loads and stores
	'ld'            :       {'type':'LOAD',},
	'ldsb'          :       {'type':'LOAD',},
	'ldsh'          :       {'type':'LOAD',},
	'ldstub'        :       {'type':'LOAD',},
	'ldub'          :       {'type':'LOAD',},
	'lduh'          :       {'type':'LOAD',},
	'ld'            :       {'type':'LOAD',},
	'ldd'           :       {'type':'LOAD',},

	# TODO: list from memory. needs to be expanded.
	'st'            :       {'type':'STORE',},
	'stb'           :       {'type':'STORE',},
	'sth'           :       {'type':'STORE',},
	'std'           :       {'type':'STORE',},
# these are also loads, but have different formats:
#	'ldf'           :       'LOAD',
#	'ldfsr'         :       'LOAD',
#	'lddf'          :       'LOAD',
#	'ldc'           :       'LOAD',
#	'ldcsr'         :       'LOAD',
#	'lddc'          :       'LOAD',
#	'ldsba'         :       'LOAD',
#	'ldsha'         :       'LOAD',
#	'lduba'         :       'LOAD',
#	'lduha'         :       'LOAD',
#	'lda'           :       'LOAD',
#	'ldda'          :       'LOAD',
#	'ldstuba'       :       'LOAD',

	# floating-point instructions
	'fitos'          :       {'type':'TWOREG'},
	'fitod'          :       {'type':'TWOREG'},
	'fitoq'          :       {'type':'TWOREG'},
	'fstoi'          :       {'type':'TWOREG'},
	'fdtoi'          :       {'type':'TWOREG'},
	'fqtoi'          :       {'type':'TWOREG'},
	'fstod'          :       {'type':'TWOREG'},
	'fstoq'          :       {'type':'TWOREG'},
	'fdtos'          :       {'type':'TWOREG'},

	'fdtoq'          :       {'type':'TWOREG'},
	'fqtod'          :       {'type':'TWOREG'},
	'fqtos'          :       {'type':'TWOREG'},
	'fmovs'          :       {'type':'TWOREG'},
	'fnegs'          :       {'type':'TWOREG'},
	'fabss'          :       {'type':'TWOREG'},
	'fsqrts'         :       {'type':'TWOREG'},
	'fsqrtd'         :       {'type':'TWOREG'},
	'fsqrtq'         :       {'type':'TWOREG'},

	'fadds'          :       {'type':'THREEREG'},
	'faddd'          :       {'type':'THREEREG'},
	'faddq'          :       {'type':'THREEREG'},
	'fsubs'          :       {'type':'THREEREG'},
	'fsubd'          :       {'type':'THREEREG'},
	'fsubq'          :       {'type':'THREEREG'},
	'fmuls'          :       {'type':'THREEREG'},
	'fmuld'          :       {'type':'THREEREG'},
	'fmulq'          :       {'type':'THREEREG'},
	'fsmuld'         :       {'type':'THREEREG'},
	'fdivs'          :       {'type':'THREEREG'},
	'fdivd'          :       {'type':'THREEREG'},
	'fdivq'          :       {'type':'THREEREG'},
	'fcmps'          :       {'type':'THREEREG'},
	'fcmpd'          :       {'type':'THREEREG'},
	'fcmpq'          :       {'type':'THREEREG'},
	'fcmpes'         :       {'type':'THREEREG'},
	'fcmped'         :       {'type':'THREEREG'},
	'fcmpeq'         :       {'type':'THREEREG'},

	# pseudo-ops
	# Argument lists for these are viciously non-uniform.
	# Anything marked 'todo' doesn't have the right format specified.
	'.alias'        :       {'type':'NOARGS'},		# compiler-generated only; ok
	'.align'        :       {'type':'ONEINT'},
	'.ascii'        :       {'type':'STRINGLIST',},
	'.asciz'        :       {'type':'STRINGLIST',},
	'.byte'         :       {'type':'INTLIST',},
	'.common'       :       {'type':'DOTCOMMON'},
	'.double'       :       {'type':'FLOATLIST',},
	'.empty'        :       {'type':'NOARGS'},
	'.file'         :       {'type':'STRINGLIST',},
	'.global'       :       {'type':'INTLIST',},
	'.globl'        :       {'type':'INTLIST',},
	'.half'         :       {'type':'INTLIST',},
	'.ident'        :       {'type':'ONESTRING'},
	'.local'        :       {'type':'INTLIST',},
	'.noalias'      :       {'type':'TWOREG'},		# compiler-generated only; ok
	'.nonvolatile'  :       {'type':'NOARGS',},
	'.nword'        :       {'type':'INTLIST',},
	'.optimstring'  :       {'type':'NOARGS'},		# compiler-generated only; ok
	'.popsection'   :       {'type':'NOARGS'},
	'.proc'         :       {'type':'ONEINT'},		# compiler-generated only; format!?
	'.pushsection'  :       {'type':'DOTSECTION'},
	'.quad'         :       {'type':'FLOATLIST',},
	'.reserve'      :       {'type':'DOTCOMMON'},
	'.section'      :       {'type':'DOTSECTION'},
	'.seg'          :       {'type':'ONEINT',},		# heh
	'.single'       :       {'type':'FLOATLIST',},
	'.size'         :       {'type':'TWOINTS'},
	'.skip'         :       {'type':'INTLIST',},
	'.stabn'        :       {'type':'ANYTHINGLIST'},
	'.stabs'        :       {'type':'ANYTHINGLIST'},
	'.type'         :       {'type':'DOTTYPE'},
	'.uahalf'       :       {'type':'INTLIST',},
	'.uaword'       :       {'type':'INTLIST',},
	'.version'      :       {'type':'ONESTRING'},
	'.volatile'     :       {'type':'NOARGS'},
	'.weak'         :       {'type':'INTLIST',},
	'.word'         :       {'type':'INTLIST',},
	'.xword'        :       {'type':'INTLIST',},
	'.xstabs'       :       {'type':'ANYTHINGLIST'},

	'.text'         :       {'type':'NOARGS'},		# what is this? it's generated by gcc
}
