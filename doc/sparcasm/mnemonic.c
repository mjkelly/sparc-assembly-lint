/*
$Log: mnemonic.c,v $
Revision 1.8  1997/03/14 05:38:54  bediger
add synonym for "bg" mnemonic: "bgt"
add ld2 and st2 mnemonics

Revision 1.7  1997/03/10 01:05:04  bediger
add 'tst' synthetic

Revision 1.6  1997/02/14 15:30:47  bediger
add btst synthetic instruction

Revision 1.5  1997/02/14 06:31:49  bediger
make many more instructions implemented.  add opcodes for some previously
unimplemented synthetic instructions.  Remove a few now-unused dummy
mnemonic instruction pointers.

Revision 1.4  1997/02/04 04:05:34  bediger
support many more synthetic instructions

Revision 1.3  1997/01/15 01:31:13  bediger
remove the .word-directive assembly: it moved back to directive

Revision 1.2  1997/01/05 08:53:13  bediger
add array entry for synthetic instruction "neg"

Revision 1.1  1996/12/13 14:32:52  bediger
Initial revision

*/
static char rcsident[] = "$Header: /home/ediger/src/csrc/sparc_assembler10/RCS/mnemonic.c,v 1.8 1997/03/14 05:38:54 bediger Exp bediger $";

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include <assy.h>
#include <assembler.h>

#ifdef USE_DMALLOC
#include <dmalloc.h>
#endif

struct mnm mnemonics[] = {
{"add",      asm_format3,        0x02, 0x00,  0x00, 0xbb, 0},  /* 0 */
{"addcc",    asm_format3,        0x02, 0x00,  0x10, 0xbb, 0},  /* 1 */
{"addx",     asm_format3,        0x02, 0x00,  0x08, 0xbb, 0},  /* 2 */
{"addxcc",   asm_format3,        0x02, 0x00,  0x18, 0xbb, 0},  /* 3 */
{"and",      asm_format3,        0x02, 0x00,  0x01, 0xbb, 0},  /* 4 */
{"andcc",    asm_format3,        0x02, 0x00,  0x11, 0xbb, 0},  /* 5 */
{"andn",     asm_format3,        0x02, 0x00,  0x05, 0xbb, 0},  /* 6 */
{"andncc",   asm_format3,        0x02, 0x00,  0x15, 0xbb, 0},  /* 7 */
{"b",        asm_branch,         0x00, 0x02,  0x08, 0xbb, 0},  /* 8 */
{"ba",       asm_branch,         0x00, 0x02,  0x08, 0xbb, 0},  /* 9 */
{"bcc",      asm_branch,         0x00, 0x02,  0x0D, 0xbb, 0},  /* 10 */
{"bclr",     asm_synth,          0x02, 0x00,  0x05, 0xbb, 0},  /* 11 */
{"bcs",      asm_branch,         0x00, 0x02,  0x05, 0xbb, 0},  /* 12 */
{"be",       asm_branch,         0x00, 0x02,  0x01, 0xbb, 0},  /* 13 */
{"beq",      asm_branch,         0x00, 0x02,  0x01, 0xbb, 0},  /* 14 */
{"bg",       asm_branch,         0x00, 0x02,  0x0A, 0xbb, 0},  /* 15 */
{"bge",      asm_branch,         0x00, 0x02,  0x0B, 0xbb, 0},  /* 16 */
{"bgeu",     asm_branch,         0x00, 0x02,  0x0D, 0xbb, 0},  /* 17 */
{"bgt",      asm_branch,         0x00, 0x02,  0x0A, 0xbb, 0},  /* 18 */
{"bgu",      asm_branch,         0x00, 0x02,  0x0C, 0xbb, 0},  /* 19 */
{"bl",       asm_branch,         0x00, 0x02,  0x03, 0xbb, 0},  /* 20 */
{"ble",      asm_branch,         0x00, 0x02,  0x02, 0xbb, 0},  /* 21 */
{"bleu",     asm_branch,         0x00, 0x02,  0x04, 0xbb, 0},  /* 22 */
{"blt",      asm_branch,         0x00, 0x02,  0x03, 0xbb, 0},  /* 23 */
{"blu",      asm_branch,         0x00, 0x02,  0x05, 0xbb, 0},  /* 24 */
{"bn",       asm_branch,         0x00, 0x02,  0x00, 0xbb, 0},  /* 25 */
{"bne",      asm_branch,         0x00, 0x02,  0x09, 0xbb, 0},  /* 26 */
{"bneg",     asm_branch,         0x00, 0x02,  0x06, 0xbb, 0},  /* 27 */
{"bnz",      asm_branch,         0x00, 0x02,  0x09, 0xbb, 0},  /* 28 */
{"bpos",     asm_branch,         0x00, 0x02,  0x0E, 0xbb, 0},  /* 29 */
{"bset",     asm_synth,          0x02, 0x00,  0x02, 0xbb, 0},  /* 30 */
{"btog",     asm_synth,          0x02, 0xff,  0x03, 0xbb, 0},  /* 31 */
{"btst",     asm_btst,           0x02, 0x00,  0x11, 0xbb, 0},  /* 32 */
{"bvc",      asm_branch,         0x00, 0x02,  0x0f, 0xbb, 0},  /* 33 */
{"bvs",      asm_branch,         0x00, 0x02,  0x07, 0xbb, 0},  /* 34 */
{"bz",       asm_branch,         0x00, 0x02,  0x01, 0xbb, 0},  /* 35 */
{"call",     asm_format1,        0x01, 0x00,  0x00, 0xbb, 0},  /* 36 */
{"cb0",      unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 37 */
{"cb01",     unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 38 */
{"cb012",    unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 39 */
{"cb013",    unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 40 */
{"cb02",     unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 41 */
{"cb023",    unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 42 */
{"cb03",     unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 43 */
{"cb1",      unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 44 */
{"cb12",     unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 45 */
{"cb123",    unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 46 */
{"cb13",     unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 47 */
{"cb2",      unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 48 */
{"cb23",     unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 49 */
{"cb3",      unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 50 */
{"cba",      unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 51 */
{"cbn",      unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 52 */
{"clr",      asm_clr_mem,        0x02, 0x00,  0x02, 0xbb, 0},  /* 53 */
{"clrb",     asm_clr_mem,        0x03, 0xff,  0x05, 0xcc, 0},  /* 54 */
{"clrh",     asm_clr_mem,        0x03, 0xff,  0x06, 0xcc, 0},  /* 55 */
{"cmp",      asm_cmp,            0x02, 0x00,  0x14, 0xbb, 0},  /* 56 */
{"cpop1",    unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 57 */
{"cpop2",    unimplemented_mnm,  0x00, 0x00,  0x00, 0xbb, 0},  /* 58 */
{"dec",      asm_inc_dec,        0x02, 0x00,  0x04, 0xbb, 0},  /* 59 */
{"deccc",    asm_inc_dec,        0x02, 0x00,  0x14, 0xbb, 0},  /* 60 */
{"fabss",    asm_format3c,       0x02, 0xff,  0x34, 0x09, 0},  /* 61 */
{"faddd",    asm_format3c,       0x02, 0xff,  0x34, 0x42, 0},  /* 62 */
{"faddq",    asm_format3c,       0x02, 0xff,  0x34, 0x09, 0},  /* 63 */
{"fadds",    asm_format3c,       0x02, 0xff,  0x34, 0x41, 0},  /* 64 */
{"fba",      asm_branch,         0x00, 0x06,  0x08, 0xbb, 0},  /* 65 */
{"fbe",      asm_branch,         0x00, 0x06,  0x09, 0xbb, 0},  /* 66 */
{"fbg",      asm_branch,         0x00, 0x06,  0x06, 0xbb, 0},  /* 67 */
{"fbge",     asm_branch,         0x00, 0x06,  0x0b, 0xbb, 0},  /* 68 */
{"fbl",      asm_branch,         0x00, 0x06,  0x04, 0xbb, 0},  /* 69 */
{"fble",     asm_branch,         0x00, 0x06,  0x0d, 0xbb, 0},  /* 70 */
{"fblg",     asm_branch,         0x00, 0x06,  0x02, 0xbb, 0},  /* 71 */
{"fbn",      asm_branch,         0x00, 0x06,  0x00, 0xbb, 0},  /* 72 */
{"fbne",     asm_branch,         0x00, 0x06,  0x01, 0xbb, 0},  /* 73 */
{"fbnz",     asm_branch,         0x00, 0x06,  0x01, 0xbb, 0},  /* 74 */
{"fbo",      asm_branch,         0x00, 0x06,  0x0f, 0xbb, 0},  /* 75 */
{"fbu",      asm_branch,         0x00, 0x06,  0x07, 0xbb, 0},  /* 76 */
{"fbue",     asm_branch,         0x00, 0x06,  0x0a, 0xbb, 0},  /* 77 */
{"fbug",     asm_branch,         0x00, 0x06,  0x05, 0xbb, 0},  /* 78 */
{"fbuge",    asm_branch,         0x00, 0x06,  0x0c, 0xbb, 0},  /* 79 */
{"fbul",     asm_branch,         0x00, 0x06,  0x03, 0xbb, 0},  /* 80 */
{"fbule",    asm_branch,         0x00, 0x06,  0x0e, 0xbb, 0},  /* 81 */
{"fbz",      asm_branch,         0x00, 0x06,  0x09, 0xbb, 0},  /* 82 */
{"fcmpd",    asm_format3c,       0x02, 0xfe,  0x35, 0x52, 0},  /* 83 */
{"fcmped",   asm_format3c,       0x02, 0xfe,  0x35, 0x56, 0},  /* 84 */
{"fcmpeq",   asm_format3c,       0x02, 0xfe,  0x35, 0x57, 0},  /* 85 */
{"fcmpes",   asm_format3c,       0x02, 0xfe,  0x35, 0x55, 0},  /* 86 */
{"fcmpq",    asm_format3c,       0x02, 0xfe,  0x35, 0x53, 0},  /* 87 */
{"fcmps",    asm_format3c,       0x02, 0xfe,  0x35, 0x51, 0},  /* 88 */
{"fdivd",    asm_format3c,       0x02, 0xff,  0x34, 0x4e, 0},  /* 89 */
{"fdivq",    asm_format3c,       0x02, 0xff,  0x34, 0x4f, 0},  /* 90 */
{"fdivs",    asm_format3c,       0x02, 0xff,  0x34, 0x4d, 0},  /* 91 */
{"fdtoi",    asm_format3c,       0x02, 0xff,  0x34, 0xd2, 0},  /* 92 */
{"fdtoq",    asm_format3c,       0x02, 0xff,  0x34, 0xce, 0},  /* 93 */
{"fdtos",    asm_format3c,       0x02, 0xff,  0x34, 0xc6, 0},  /* 94 */
{"fitod",    asm_format3c,       0x02, 0xff,  0x34, 0xc8, 0},  /* 95 */
{"fitoq",    asm_format3c,       0x02, 0xff,  0x34, 0xcc, 0},  /* 96 */
{"fitos",    asm_format3c,       0x02, 0xff,  0x34, 0xc4, 0},  /* 97 */
{"flush",    asm_clr_mem,        0x02, 0xff,  0x3b, 0xbb, 0},  /* 98 */
{"fmovs",    asm_format3c,       0x02, 0xff,  0x34, 0x01, 0},  /* 99 */
{"fmuld",    asm_format3c,       0x02, 0xff,  0x34, 0x4a, 0},  /* 100 */
{"fmulq",    asm_format3c,       0x02, 0xff,  0x34, 0x4b, 0},  /* 101 */
{"fmuls",    asm_format3c,       0x02, 0xff,  0x34, 0x49, 0},  /* 102 */
{"fnegs",    asm_format3c,       0x02, 0xff,  0x34, 0x05, 0},  /* 103 */
{"fqtod",    asm_format3c,       0x02, 0xff,  0x34, 0xcb, 0},  /* 104 */
{"fqtoi",    asm_format3c,       0x02, 0xff,  0x34, 0xd3, 0},  /* 105 */
{"fqtos",    asm_format3c,       0x02, 0xff,  0x34, 0xc7, 0},  /* 106 */
{"fsmuld",   asm_format3c,       0x02, 0xff,  0x34, 0x69, 0},  /* 107 */
{"fsmulq",   asm_format3c,       0x02, 0xff,  0x34, 0x6e, 0},  /* 108 */
{"fsqrtd",   asm_format3c,       0x02, 0xff,  0x34, 0x2a, 0},  /* 109 */
{"fsqrtq",   asm_format3c,       0x02, 0xff,  0x34, 0x2b, 0},  /* 110 */
{"fsqrts",   asm_format3c,       0x02, 0xff,  0x34, 0x29, 0},  /* 111 */
{"fstod",    asm_format3c,       0x02, 0xff,  0x34, 0xC9, 0},  /* 112 */
{"fstoi",    asm_format3c,       0x02, 0xff,  0x34, 0xD1, 0},  /* 113 */
{"fstoq",    asm_format3c,       0x02, 0xff,  0x34, 0xCD, 0},  /* 114 */
{"fsubd",    asm_format3c,       0x02, 0xff,  0x34, 0x46, 0},  /* 115 */
{"fsubq",    asm_format3c,       0x02, 0xff,  0x34, 0x47, 0},  /* 116 */
{"fsubs",    asm_format3c,       0x02, 0xff,  0x34, 0x45, 0},  /* 117 */
{"iflush",   asm_clr_mem,        0x02, 0xff,  0x3b, 0xbb, 0},  /* 118 */
{"inc",      asm_inc_dec,        0x02, 0x00,  0x00, 0xbb, 0},  /* 119 */
{"inccc",    asm_inc_dec,        0x02, 0x00,  0x10, 0xbb, 0},  /* 120 */
{"jmp",      asm_jmp,            0x02, 0xff,  0x38, 0xbb, 0},  /* 121 */
{"jmpl",     asm_load,           0x02, 0xff,  0x38, 0xbb, 0},  /* 122 */
{"ld",       asm_load,           0x03, 0xff,  0x00, 0xbb, 0},  /* 123 */
{"ld2",      asm_ld2,            0x03, 0xff,  0x20, 0xbb, 0},  /* 124 */
{"lda",      asm_load,           0x03, 0xff,  0x10, 0xbb, 0},  /* 125 */
{"ldc",      asm_load,           0x03, 0xff,  0x30, 0xbb, 0},  /* 126 */
{"ldcsr",    asm_load,           0x03, 0xff,  0x31, 0xbb, 0},  /* 127 */
{"ldd",      asm_load,           0x03, 0xff,  0x03, 0xbb, 0},  /* 128 */
{"ldda",     asm_load,           0x03, 0xff,  0x13, 0xbb, 0},  /* 129 */
{"lddc",     asm_load,           0x03, 0xff,  0x33, 0xbb, 0},  /* 130 */
{"lddf",     asm_load,           0x03, 0xff,  0x23, 0xbb, 0},  /* 131 */
{"ldf",      asm_load,           0x03, 0xff,  0x20, 0xbb, 0},  /* 132 */
{"ldfsr",    asm_load,           0x03, 0xff,  0x21, 0xbb, 0},  /* 133 */
{"ldsb",     asm_load,           0x03, 0xff,  0x09, 0xbb, 0},  /* 134 */
{"ldsba",    asm_load,           0x03, 0xff,  0x19, 0xbb, 0},  /* 135 */
{"ldsh",     asm_load,           0x03, 0xff,  0x0A, 0xbb, 0},  /* 136 */
{"ldsha",    asm_load,           0x03, 0xff,  0x1A, 0xbb, 0},  /* 137 */
{"ldstub",   asm_load,           0x03, 0xff,  0x0D, 0xbb, 0},  /* 138 */
{"ldstuba",  asm_load,           0x03, 0xff,  0x1d, 0xbb, 0},  /* 139 */
{"ldub",     asm_load,           0x03, 0xff,  0x01, 0xbb, 0},  /* 140 */
{"lduba",    asm_load,           0x03, 0xff,  0x11, 0xbb, 0},  /* 141 */
{"lduh",     asm_load,           0x03, 0xff,  0x02, 0xbb, 0},  /* 142 */
{"lduha",    asm_load,           0x03, 0xff,  0x12, 0xbb, 0},  /* 143 */
{"mov",      asm_mov,            0x02, 0xff,  0x00, 0xbb, 0},  /* 144 */
{"mulscc",   asm_format3,        0x02, 0x00,  0x24, 0xbb, 0},  /* 145 */
{"neg",      asm_neg,            0x02, 0x00,  0x04, 0xbb, 0},  /* 146 */
{"nop",      asm_nop,            0x02, 0x04,  0x00, 0xbb, 0},  /* 147 */
{"not",      asm_not,            0x02, 0xff,  0x07, 0xbb, 0},  /* 148 */
{"or",       asm_format3,        0x02, 0x00,  0x02, 0xbb, 0},  /* 149 */
{"orcc",     asm_format3,        0x02, 0x00,  0x12, 0xbb, 0},  /* 150 */
{"orn",      asm_format3,        0x02, 0x00,  0x06, 0xbb, 0},  /* 151 */
{"orncc",    asm_format3,        0x02, 0x00,  0x16, 0xbb, 0},  /* 152 */
{"rd",       asm_rd,             0x02, 0xff,  0x00, 0xbb, 0},  /* 153 */
{"restore",  asm_format3,        0x02, 0x00,  0x3d, 0xbb, 0},  /* 154 */
{"ret",      asm_ret,            0xff, 0xff,  0xff, 0xbb, 0},  /* 155 */
{"retl",     asm_retl,           0x00, 0xff,  0xff, 0xbb, 0},  /* 156 */
{"rett",     asm_clr_mem,        0x02, 0xff,  0x39, 0xbb, 0},  /* 157 */
{"save",     asm_format3,        0x02, 0x00,  0x3c, 0xbb, 0},  /* 158 */
{"sdiv",     asm_format3,        0x02, 0x00,  0x0f, 0xbb, 0},  /* 159 */
{"sdivcc",   asm_format3,        0x02, 0x00,  0x1f, 0xbb, 0},  /* 160 */
{"set",      asm_set,            0x00, 0xff,  0x00, 0xbb, 0},  /* 161 */
{"sethi",    asm_sethi,          0x00, 0x04,  0x00, 0xbb, 0},  /* 162 */
{"sll",      asm_format3,        0x02, 0x00,  0x25, 0xbb, 0},  /* 163 */
{"smul",     asm_format3,        0x02, 0x00,  0x0b, 0xbb, 0},  /* 164 */
{"smulcc",   asm_format3,        0x02, 0x00,  0x1b, 0xbb, 0},  /* 165 */
{"sra",      asm_format3,        0x02, 0x00,  0x27, 0xbb, 0},  /* 166 */
{"srl",      asm_format3,        0x02, 0x00,  0x26, 0xbb, 0},  /* 167 */
{"st",       asm_load,           0x03, 0xff,  0x04, 0xcc, 0},  /* 168 */
{"st2",      asm_ld2,            0x03, 0xff,  0x24, 0xcc, 0},  /* 169 */
{"sta",      asm_load,           0x03, 0xff,  0x14, 0xcc, 0},  /* 170 */
{"stb",      asm_load,           0x03, 0xff,  0x05, 0xcc, 0},  /* 171 */
{"stba",     asm_load,           0x03, 0xff,  0x15, 0xcc, 0},  /* 172 */
{"stbar",    unimplemented_mnm,  0x02, 0xff,  0x28, 0xbb, 0},  /* 173 */
{"stc",      asm_load,           0x03, 0xff,  0x34, 0xcc, 0},  /* 174 */
{"stcsr",    asm_load,           0x03, 0xff,  0x35, 0xcc, 0},  /* 175 */
{"std",      asm_load,           0x03, 0xff,  0x07, 0xcc, 0},  /* 176 */
{"stda",     asm_load,           0x03, 0xff,  0x17, 0xcc, 0},  /* 177 */
{"stdc",     asm_load,           0x03, 0xff,  0x37, 0xcc, 0},  /* 178 */
{"stdcq",    asm_load,           0x03, 0xff,  0x36, 0xcc, 0},  /* 179 */
{"stdf",     asm_load,           0x03, 0xff,  0x27, 0xcc, 0},  /* 180 */
{"stdfq",    asm_load,           0x03, 0xff,  0x26, 0xcc, 0},  /* 181 */
{"stf",      asm_load,           0x03, 0xff,  0x24, 0xcc, 0},  /* 182 */
{"stfsr",    asm_load,           0x03, 0xff,  0x25, 0xcc, 0},  /* 183 */
{"sth",      asm_load,           0x03, 0xff,  0x06, 0xcc, 0},  /* 184 */
{"stha",     asm_load,           0x03, 0xff,  0x16, 0xcc, 0},  /* 185 */
{"sub",      asm_format3,        0x02, 0x00,  0x04, 0xbb, 0},  /* 186 */
{"subcc",    asm_format3,        0x02, 0x00,  0x14, 0xbb, 0},  /* 187 */
{"subx",     asm_format3,        0x02, 0x00,  0x0c, 0xbb, 0},  /* 188 */
{"subxcc",   asm_format3,        0x02, 0x00,  0x1c, 0xbb, 0},  /* 189 */
{"swap",     asm_load,           0x03, 0xff,  0x0f, 0xbb, 0},  /* 190 */
{"swapa",    asm_load,           0x03, 0xff,  0x1f, 0xbb, 0},  /* 191 */
{"t",        asm_trap,           0x02, 0x08,  0x3a, 0xbb, 0},  /* 192 */
{"ta",       asm_trap,           0x02, 0x08,  0x3a, 0xbb, 0},  /* 193 */
{"taddcc",   asm_format3,        0x02, 0x00,  0x20, 0xbb, 0},  /* 194 */
{"taddcctv", asm_format3,        0x02, 0x00,  0x22, 0xbb, 0},  /* 195 */
{"tcc",      asm_trap,           0x02, 0x0d,  0x3a, 0xbb, 0},  /* 196 */
{"tcs",      asm_trap,           0x02, 0x05,  0x3a, 0xbb, 0},  /* 197 */
{"te",       asm_trap,           0x02, 0x01,  0x3a, 0xbb, 0},  /* 198 */
{"tg",       asm_trap,           0x02, 0x0a,  0x3a, 0xbb, 0},  /* 199 */
{"tge",      asm_trap,           0x02, 0x0b,  0x3a, 0xbb, 0},  /* 200 */
{"tgeu",     asm_trap,           0x02, 0x0d,  0x3a, 0xbb, 0},  /* 201 */
{"tgu",      asm_trap,           0x02, 0x0c,  0x3a, 0xbb, 0},  /* 202 */
{"tl",       asm_trap,           0x02, 0x03,  0x3a, 0xbb, 0},  /* 203 */
{"tle",      asm_trap,           0x02, 0x02,  0x3a, 0xbb, 0},  /* 204 */
{"tleu",     asm_trap,           0x02, 0x04,  0x3a, 0xbb, 0},  /* 205 */
{"tlu",      asm_trap,           0x02, 0x05,  0x3a, 0xbb, 0},  /* 206 */
{"tn",       asm_trap,           0x02, 0x00,  0x3a, 0xbb, 0},  /* 207 */
{"tne",      asm_trap,           0x02, 0x09,  0x3a, 0xbb, 0},  /* 208 */
{"tneg",     asm_trap,           0x02, 0x06,  0x3a, 0xbb, 0},  /* 209 */
{"tnz",      asm_trap,           0x02, 0x09,  0x3a, 0xbb, 0},  /* 210 */
{"tpos",     asm_trap,           0x02, 0x0e,  0x3a, 0xbb, 0},  /* 211 */
{"tst",      asm_tst,            0x02, 0x00,  0x12, 0xbb, 0},  /* 212 */
{"tsubcc",   asm_format3,        0x02, 0xff,  0x21, 0xbb, 0},  /* 213 */
{"tsubcctv", asm_format3,        0x02, 0xff,  0x23, 0xbb, 0},  /* 214 */
{"tvc",      asm_trap,           0x02, 0x0f,  0x3a, 0xbb, 0},  /* 215 */
{"tvs",      asm_trap,           0x02, 0x07,  0x3a, 0xbb, 0},  /* 216 */
{"tz",       asm_trap,           0x02, 0x01,  0x3a, 0xbb, 0},  /* 217 */
{"udiv",     asm_format3,        0x02, 0xff,  0x0e, 0xbb, 0},  /* 218 */
{"udivcc",   asm_format3,        0x02, 0xff,  0x1e, 0xbb, 0},  /* 219 */
{"umul",     asm_format3,        0x02, 0xff,  0x0a, 0xbb, 0},  /* 220 */
{"umulcc",   asm_format3,        0x02, 0xff,  0x1a, 0xbb, 0},  /* 221 */
{"unimp",    asm_branch,         0x00, 0x00,  0x00, 0xbb, 0},  /* 222 */
{"wr",       asm_wr,             0x02, 0xff,  0xff, 0xbb, 0},  /* 223 */
{"xnor",     asm_format3,        0x02, 0xff,  0x07, 0xbb, 0},  /* 224 */
{"xnorcc",   asm_format3,        0x02, 0xff,  0x17, 0xbb, 0},  /* 225 */
{"xor",      asm_format3,        0x02, 0xff,  0x03, 0xbb, 0},  /* 226 */
};

/* these are in this file to keep everything together */
struct mnm rdy   = {"RDY",      asm_format3,      0x02, 0xff,  0x28, 0xbb, 0};
struct mnm rdpsr = {"RDPSR",    asm_format3,      0x02, 0xff,  0x29, 0xbb, 0};
struct mnm rdwim = {"RDWIM",    asm_format3,      0x02, 0xff,  0x2A, 0xbb, 0};
struct mnm rdtbr = {"RDTBR",    asm_format3,      0x02, 0xff,  0x2B, 0xbb, 0};

struct mnm wry   = {"WRY",      asm_format3,      0x02, 0xff,  0x30, 0xbb, 0};
struct mnm wrpsr = {"WRPSR",    asm_format3,      0x02, 0xff,  0x31, 0xbb, 0};
struct mnm wrwim = {"WRWIM",    asm_format3,      0x02, 0xff,  0x32, 0xbb, 0};
struct mnm wrtbr = {"WRTBR",    asm_format3,      0x02, 0xff,  0x33, 0xbb, 0};

/* this is hideous: it circumvents the idea of keeping things
 * consistent by having only one instance.  I guess it keeps
 * 2 instances from getting out-of-sync, but it's a maintenance prob */

struct mnm *jmpl_dummy  = &mnemonics[122];
struct mnm *ld2_dummy   = &mnemonics[124];
struct mnm *ldc_dummy   = &mnemonics[125];
struct mnm *ldcsr_dummy = &mnemonics[127];
struct mnm *lddc_dummy  = &mnemonics[130];
struct mnm *lddf_dummy  = &mnemonics[131];
struct mnm *ldf_dummy   = &mnemonics[132];
struct mnm *ldfsr_dummy = &mnemonics[133];
struct mnm *or_dummy    = &mnemonics[149];
struct mnm *set_dummy   = &mnemonics[161];
struct mnm *sethi_dummy = &mnemonics[162];
struct mnm *st_dummy    = &mnemonics[168];
struct mnm *st2_dummy   = &mnemonics[169];
struct mnm *stc_dummy   = &mnemonics[174];
struct mnm *stcsr_dummy = &mnemonics[175];
struct mnm *stdc_dummy  = &mnemonics[178];
struct mnm *stdcq_dummy = &mnemonics[179];
struct mnm *stdf_dummy  = &mnemonics[180];
struct mnm *stdfq_dummy = &mnemonics[181];
struct mnm *stf_dummy   = &mnemonics[182];
struct mnm *stfsr_dummy = &mnemonics[183];
struct mnm *rdy_dummy   = &rdy;
struct mnm *rdpsr_dummy = &rdpsr;
struct mnm *rdwim_dummy = &rdwim;
struct mnm *rdtbr_dummy = &rdtbr;
struct mnm *wry_dummy   = &wry;
struct mnm *wrpsr_dummy = &wrpsr;
struct mnm *wrwim_dummy = &wrwim;
struct mnm *wrtbr_dummy = &wrtbr;

int
mnm_cmp(const void *key, const void *array_element)
{
	const struct mnm *p = array_element;
    return strcmp(key, p->op_mnm);
}

struct mnm *
is_mnemonic(char *s)
{
	struct mnm *p;

	assert(NULL != s);

	p = bsearch(
		(void *)s,
		(void *)mnemonics,
		sizeof(mnemonics)/sizeof(*mnemonics),
		sizeof(*mnemonics),
		mnm_cmp
	);

	return p;
}
