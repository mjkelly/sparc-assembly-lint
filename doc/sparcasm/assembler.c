/*
 *
$Log: assembler.c,v $
Revision 1.18  1997/03/21 07:44:04  bediger
Make disp22 and disp30 fields of CALL and BRANCH instructions
work even if the instruction or destination is in a different
(non-.text) segment.

Revision 1.17  1997/03/14 05:43:58  bediger
add code to handle ld2 and st2 synthetic instructions.

Revision 1.16  1997/03/10 01:18:01  bediger
bug fix for "op imm,r1,rd" when it has relocation info with the immediate

Revision 1.15  1997/03/09 02:48:18  bediger
1. make "symbol = expression" symbols be N_ABS
2. Add %fq register support
3. Fix a bug in the generation of sethi/or pairs from a set synthetic
4. Make it do 'tst' synthetic as gas does it, not as book says to
5. Guard against NULL reloc info from N_ABS symbols

Revision 1.14  1997/02/14 15:30:10  bediger
add btst synthetic instruction

Revision 1.13  1997/02/14 06:18:25  bediger
complete functions to assemble rd and wr mnemonics, fix asm_format1()
for the case of a non-symbolic immediate, make assembly of unimp
instruction work right, fix up assembly of format 3c floating point
mnemonics, keep from smashing a few previously-allocated pointers.

Revision 1.12  1997/02/04 05:58:34  bediger
correct a bug with 'set' instruction relocation information.

Revision 1.11  1997/02/04 03:57:10  bediger
support many more synthetic instructions.  support re-arranged
assembly statement representation.

Revision 1.10  1997/01/15 01:25:32  bediger
partially fixed a memory leak in asm_ret(), made .word-directive
function back into a "directive", added "symbol = expression" function

Revision 1.9  1997/01/05 08:55:41  bediger
add use of convenience macros IS_SYMBOL_TYPE(), correct a bug in
asm_branch() that made relocations into absolute RELOC_22 types
instead of PC-relative RELOC_WDISP22 types. add asm_neg() function
for assembling synthetic instruction neg.

Revision 1.8  1997/01/01 22:07:42  bediger
made every "immediate" field of instruction be the "value" of
expr_to_imm() expression tree traversal

Revision 1.7  1996/12/29 01:20:49  bediger
support for cmd-line specification of symbol table debugging

Revision 1.6  1996/12/19 06:50:54  bediger
added stuff to deal with 3-address instructions that look like:
add -16,%r1,%r2
which is pretty much against the "suggested assembler syntax".

Revision 1.5  1996/12/17 06:32:10  bediger
minor changes to reflect extra operations that may appear in parse trees
as a result of adding all unary and binary ops from SunOS assembler.
Addition of 'case' keywords that had been missing from a switch over
enum ExprNodeT: the compiler picked up the enums as labels.

Revision 1.4  1996/12/13 14:32:52  bediger
switched over to dynamic register representation, which uncovered
a bug in asm_load()'s manipulation of the struct assy_stmnt into
what's expected by asm_format3().

Revision 1.3  1996/12/13 06:20:42  bediger
this very is buggy, checkin before major surgery

Revision 1.2  1996/12/12 19:55:07  bediger
a version that handles the ld [...],%f0, ld [...],%c1, ld [...],%csr
one-mnemonic-for-many-opcodes problem in a most ungracious manner

 *
 */
static char rcsident[] = "$Header: /home/ediger/src/csrc/sparc_assembler10/RCS/assembler.c,v 1.18 1997/03/21 07:44:04 bediger Exp bediger $";

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <errno.h>
#include <a.out.h>

#include <assy.h>
#include <io.h>
#include <assembler.h>
#include <formats.h>
#include <symtable.h>  /* for insert_relocation() prototype */
#include <expr.h>
#include <shortcut_alloc.h>

#ifdef USE_DMALLOC
#include <dmalloc.h>
#endif

void write_instn(int *instn);
int real_asm_nop(void);
int asm_set_numeric(struct asm_stmnt *stmnt);
int asm_set_symbolic(struct asm_stmnt *stmnt);

extern struct mnm *sethi_dummy;
extern struct mnm *or_dummy;
extern struct mnm *sub_dummy;
extern struct mnm *jmpl_dummy;
extern struct mnm *st_dummy;

extern struct mnm *stdf_dummy;
extern struct mnm *stdfq_dummy;
extern struct mnm *stfsr_dummy;
extern struct mnm *stf_dummy;
extern struct mnm *stc_dummy;
extern struct mnm *stdc_dummy;
extern struct mnm *stcsr_dummy;

extern struct mnm *lddf_dummy;
extern struct mnm *lddfq_dummy;
extern struct mnm *ldfsr_dummy;
extern struct mnm *ldf_dummy;
extern struct mnm *ldc_dummy;
extern struct mnm *lddc_dummy;
extern struct mnm *ldcsr_dummy;
extern struct mnm *rdy_dummy;
extern struct mnm *rdpsr_dummy;
extern struct mnm *rdwim_dummy;
extern struct mnm *rdtbr_dummy;
extern struct mnm *wry_dummy;
extern struct mnm *wrpsr_dummy;
extern struct mnm *wrwim_dummy;
extern struct mnm *wrtbr_dummy;

struct register_rep reg_g0_dummy = { REGULAR, 0 };
struct register_rep reg_o7_dummy = { REGULAR, 15 };
struct register_rep reg_i7_dummy = { REGULAR, 31 };

extern struct mem_stack register_alloc;
extern struct mem_stack int_alloc;

extern int text_size;
#define CURRADDR ((TEXT_SEG==current_segment)?outs_offset[TEXT_SEG]:text_size+outs_offset[DATA_SEG]) 

/* catchall - output to notify that some mnemonic or synthic instruction isn't
 * implemented yet
 */
int
unimplemented_mnm(struct asm_stmnt  *stmnt)
{
	assert(NULL != stmnt);

	input_problem("unimplemented mnemonic \"%s\"\n",
		stmnt->mnemonic->op_mnm);

	return real_asm_nop();
}

/* asm_rd() exists because of the "suggested assembly language syntax".
 * RDY, RDASR, RDPSR, RDWIM, RDTBR all have different op3 fields,
 * but have the same mnemonic, "rd".  That means setting op3 based on
 * the single operand register name.
 */
int
asm_rd(struct asm_stmnt  *stmnt)
{
	assert(NULL != stmnt);

	ASM_ALLOC(stmnt->rs2, register_alloc, struct register_rep);
	stmnt->rs2->type = REGULAR;
	stmnt->rs2->regno = 0;

	/* switch on the type of "special" register 1st address */
	switch (stmnt->rs1->type)
	{
	case Y:   stmnt->mnemonic = rdy_dummy;   stmnt->rs1->regno = 0; break;
	case ASR: stmnt->mnemonic = rdy_dummy;                          break;
	case PSR: stmnt->mnemonic = rdpsr_dummy; stmnt->rs1->regno = 0; break;
	case WIM: stmnt->mnemonic = rdwim_dummy; stmnt->rs1->regno = 0; break;
	case TBR: stmnt->mnemonic = rdtbr_dummy; stmnt->rs1->regno = 0; break;
	default:
		input_problem("Extremely goofy rd instruction\n");
		return real_asm_nop();
		break;
	}

	return asm_format3(stmnt);
}

int
asm_wr(struct asm_stmnt  *stmnt)
{
	assert(NULL != stmnt);

	if (!stmnt->immediate && !stmnt->rs2)
	{
		ASM_ALLOC(stmnt->rs2, register_alloc, struct register_rep);
		stmnt->rs2->type = REGULAR;
		stmnt->rs2->regno = 0;
	}

	if (stmnt->rd->type != ASR)
		stmnt->rd->regno = 0;

	switch (stmnt->rd->type)
	{
	case Y:   stmnt->mnemonic = wry_dummy;    break;
	case ASR: stmnt->mnemonic = wry_dummy;    break;
	case PSR: stmnt->mnemonic = wrpsr_dummy;  break;
	case WIM: stmnt->mnemonic = wrwim_dummy;  break;
	case TBR: stmnt->mnemonic = wrtbr_dummy;  break;
	default:
		input_problem("Extremely goofy wr instruction\n");
		return real_asm_nop();
		break;
	}

	return asm_format3(stmnt);
}

int
asm_format1(struct asm_stmnt *stmnt)
{
	struct format1 instn;

	assert(NULL != stmnt);

	/* how do I tell? */
	if (NULL != stmnt->rs1 || NULL != stmnt->rs2)
	{
		/* table A-1, SPARC v8 synthetic instructions: call _address_ 
		 * where _address_ has a register named in it.  Assembles as
		 * jmpl address, %o7 */

		stmnt->mnemonic = jmpl_dummy;
		if (!stmnt->rd)
			ASM_ALLOC(stmnt->rd, register_alloc, struct register_rep);
		stmnt->rd->regno = 15;

		return asm_load(stmnt);
	}

	instn.op = stmnt->mnemonic->op;

	if (stmnt->symbol)
	{
		if (IS_SYMBOL_TYPE(stmnt->symbol, CURR_SEG_TYPE))
		{
			/* PC-relative, no need to have a relocation record since
			 * the call destination is in this segment */

			if (stmnt->immediate)
				instn.disp30 = ((*stmnt->immediate - CURRADDR) >> 2);
			else if (stmnt->symbol)
				instn.disp30 = (stmnt->symbol->n_value - CURRADDR) >> 2;
			else
				instn.disp30 = (0 - CURRADDR) >> 2;

			if (stmnt->reloc)
			{
				free(stmnt->reloc);
				stmnt->reloc = NULL;
			}
		} else {
			if (stmnt->reloc)
			{
				stmnt->reloc->r_type = RELOC_WDISP30;
				stmnt->reloc->r_addend = 0 - CURROFFSET;
				insert_relocation(__FILE__, __LINE__, stmnt->reloc, stmnt->symbol);
			}

			instn.disp30 = (stmnt->symbol->n_value) >> 2;
		}
	} else {
		instn.disp30 = ((*stmnt->immediate - CURRADDR) >> 2);
	}

	write_instn((int *)&instn);

	return 1;
}

/* branches are also format 2 instructions, but there's enough weirdness
 * to them that you can't use a generic "assemble format 2" routine on
 * them.  One of the weird things is the use of the "rd" field as yet
 * another part of the opcode, the "cond".
 */
int
asm_branch(struct asm_stmnt *stmnt)
{
	struct format2 instn;

	assert(NULL != stmnt);

	instn.op = stmnt->mnemonic->op;

	/* here's where op3 field of struct mnm is used as cond field,
	 * and that's why asm_branch() is not the same as asm_format2() */
	instn.rd = stmnt->mnemonic->op3;
	if (stmnt->mnemonic->anul_bit)
		instn.rd |= 0x10;  /* set anul bit on instn.rd field */
	instn.op2 = stmnt->mnemonic->op2;

	if (stmnt->symbol)
	{
		if (IS_SYMBOL_TYPE(stmnt->symbol, CURR_SEG_TYPE))
		{
			instn.imm22 = (*stmnt->immediate + stmnt->reloc->r_addend - CURRADDR) >> 2;
			free(stmnt->reloc);
		} else {
			if (stmnt->reloc)
			{
				if (RELOC_UNUSED3 == stmnt->reloc->r_type)
					stmnt->reloc->r_type = RELOC_WDISP22;
				stmnt->reloc->r_addend = 0 - CURROFFSET;
				insert_relocation(__FILE__, __LINE__, stmnt->reloc, stmnt->symbol);
			}

			/* this is kind of bogus, since it will be overwritten during
			 * relocation, but it makes output exactly like GAS output. */
			instn.imm22 = ((stmnt->symbol->n_value - CURRADDR)/4 & 0x3FFFFF);
		}

	} else {

		if (!strcmp(stmnt->mnemonic->op_mnm, "unimp"))
			if (stmnt->immediate)
				instn.imm22 = *stmnt->immediate;
			else
				instn.imm22 = 0;
		else {
			/* this appears to be a violation of the "suggested assembly
			 * language syntax" in that a branch mnemonic is only supposed
			 * to have a label not a constant address - but GAS accepts it. */
			instn.imm22 = (*stmnt->immediate - CURROFFSET) >> 2;
		}
	}

	write_instn((int *)&instn);

	return 1;
}

int
asm_format3(struct asm_stmnt *stmnt)
{
	struct format3a instn3a;
	struct format3b instn3b;
	int *x, flag = 0;

	assert(NULL != stmnt);

	if (!strcmp("restore", stmnt->mnemonic->op_mnm) ||
		!strcmp("save", stmnt->mnemonic->op_mnm))
	{
		if (NULL == stmnt->rs1 && NULL == stmnt->rs1 &&  NULL == stmnt->rd)
		{
			/* this is a cheat */
			memset((void *)&instn3a, 0, sizeof(instn3a));
			instn3a.op = stmnt->mnemonic->op;
			instn3a.op3 = stmnt->mnemonic->op3;

			write_instn((int *)&instn3a);

			return 1;
		}
	}

	instn3a.op  = instn3b.op  = stmnt->mnemonic->op;
	instn3a.op3 = instn3b.op3 = stmnt->mnemonic->op3;
	instn3a.rd  = instn3b.rd  = stmnt->rd->regno;
	if (stmnt->rs1)
		instn3a.rs1 = instn3b.rs1 = stmnt->rs1->regno;
	else
		instn3a.rs1 = instn3b.rs1 = 0;  /* implied %g0 */

	if (stmnt->rs2)       flag |= 4;
	if (stmnt->symbol)    flag |= 2;
	if (stmnt->immediate) flag |= 1;

	switch (flag)
	{
	case 5:  /* icky special case: op imm,r1,rd - lcc does this. */
	case 7:  /* icky special case: op sym,r1,rd */
		instn3b.rs1 = stmnt->rs2->regno;
		/* FALL THROUGH */

	case 1: case 2: case 3:  /* r1,imm,rd or r1,sym,rd */
		instn3b.i = 1;

		if (-1 != stmnt->asi)
			input_problem("%s instruction, ASI of %d can't be here.\n", 
				stmnt->mnemonic->op_mnm,
				stmnt->asi);

		if (stmnt->reloc)
		{
			if (RELOC_UNUSED3 == stmnt->reloc->r_type)
				stmnt->reloc->r_type = RELOC_13;
			insert_relocation(__FILE__, __LINE__, stmnt->reloc, stmnt->symbol);
			instn3b.simm13 = 0;  /* taken care of in relocation */
		} else if (stmnt->immediate)
			instn3b.simm13 = *stmnt->immediate;
		else
			instn3b.simm13 = 0;

		x = (int *)&instn3b; break;

	case 4:                  /* r1,r2,rd  */
		instn3a.i = 0;

		instn3a.rs2 = stmnt->rs2->regno;

		/* ASI instructions only non-immediate forms */
		if (-1 != stmnt->asi)
			instn3a.asi = stmnt->asi;
		else 
			instn3a.asi = 0;

		x = (int *)&instn3a;
		break;

	default:
		internal_problem(__FILE__, __LINE__, "%s: Incredibly horrible error\n", stmnt->mnemonic->op_mnm);
		return real_asm_nop();
		break;
	}

	write_instn(x);

	return 1;
}

/* asm_format3c() - assembly of floating point opcodes.
 * fp ops are again a bit unusual: the ASI field is used as another
 * partial opcode.  */
int
asm_format3c(struct asm_stmnt *stmnt)
{
	if (!stmnt->rs2)
	{	
		if (0xff == stmnt->mnemonic->op2)
		{
			/* mnemonic freg_rs2,freg_rd */
			stmnt->rs2 = stmnt->rs1;
			stmnt->rs1 = NULL;
		} else {
			/* mnemonic freg_rs1,freg_rs2 */
			stmnt->rs2 = stmnt->rd;
			ASM_ALLOC(stmnt->rd, register_alloc, struct register_rep);
			stmnt->rd->type  = REGULAR;
			stmnt->rd->regno = 0;
		}
	}

	stmnt->asi = stmnt->mnemonic->opf;

	return asm_format3(stmnt);
}

/* trap instructions use a weird form of format 3a and 3b:
 * the rd field of formats 3a and 3b is 5 bits, 4 of which
 * are used to indicate the trap "cond".  asm_trap() covers
 * up the use of rd field by filling in a "phony" asm_address
 * with a register number that is actually the "cond" field.
 * In turn, the "cond" field is taken from the op2 field of the
 * struct mnm, which represents the opcode mnemonic.
 */

int
asm_trap(struct asm_stmnt *stmnt)
{
	assert(NULL != stmnt);
	ASM_ALLOC(stmnt->rd, register_alloc, struct register_rep);
	stmnt->rd->regno = (stmnt->mnemonic->op2 & 0xf);
	return asm_load(stmnt);
}

/*
 * asm_ret() and asm_retl() handle some synthetic instructions
 * that map directly into jmpl variants.
 */

int
asm_ret_retl(struct asm_stmnt *stmnt, int regno)
{
	assert(NULL != stmnt);

	stmnt->mnemonic = jmpl_dummy;
	ASM_ALLOC(stmnt->rs1, register_alloc, struct register_rep);
	ASM_ALLOC(stmnt->rd,  register_alloc, struct register_rep);

	stmnt->rs1->type  = REGULAR;
	stmnt->rs1->regno = regno;
	stmnt->rs2 = NULL;
	stmnt->rd->type   = REGULAR;
	stmnt->rd->regno  = 0;

	if (!stmnt->immediate)
		ASM_ALLOC(stmnt->immediate, int_alloc, int);
	*stmnt->immediate = 8;

	stmnt->reloc = NULL;
	stmnt->symbol = NULL;
	stmnt->asi = -1;

	return asm_load(stmnt);
}

int
asm_ret(struct asm_stmnt *stmnt)
{
	return asm_ret_retl(stmnt, 31);
}

int
asm_retl(struct asm_stmnt *stmnt)
{
	return asm_ret_retl(stmnt, 15);
}

int
asm_jmp(struct asm_stmnt *stmnt)
{
	assert(NULL != stmnt);

	ASM_ALLOC(stmnt->rd, register_alloc, struct register_rep);
	stmnt->rd->type = REGULAR;
	stmnt->rd->regno = 0;

	if (!stmnt->immediate && !stmnt->symbol && !stmnt->rs2)
	{
		ASM_ALLOC(stmnt->rs2, register_alloc, struct register_rep);
		stmnt->rs2->type = REGULAR;
		stmnt->rs2->regno = 0;
	}

	return asm_load(stmnt);
}

/* cmp rs1,reg_or_imm -> subcc rs1,reg_or_imm,%g0 */
int
asm_cmp(struct asm_stmnt *stmnt)
{
	assert(NULL != stmnt);

	stmnt->rs2 = stmnt->rd;

	ASM_ALLOC(stmnt->rd, register_alloc, struct register_rep);
	stmnt->rd->type  = REGULAR;
	stmnt->rd->regno = 0;

	return asm_format3(stmnt);
}

/* not rs1,rd  ->  xnor rs1,%g0,rd
 * not rd      ->  xnor  rd,%g0,rd
 */
int
asm_not(struct asm_stmnt *stmnt)
{
	assert(NULL != stmnt);

	ASM_ALLOC(stmnt->rs2, register_alloc, struct register_rep);
	stmnt->rs2->type  = REGULAR;
	stmnt->rs2->regno = 0;

	/* how to distinguish 'not rs1,rd', from 'not rd'? */
	if (!stmnt->rd)
	{
		ASM_ALLOC(stmnt->rd, register_alloc, struct register_rep);
		stmnt->rd->type  = stmnt->rs1->type;
		stmnt->rd->regno = stmnt->rs1->regno;
	}

	return asm_format3(stmnt);
}

/* bset|bclr|btog reg-or-imm,rd -> opcode rd,reg-or-imm,rd */
int
asm_synth(struct asm_stmnt *stmnt)
{
	assert(NULL != stmnt);

	stmnt->rs2 = stmnt->rs1;
	
	ASM_ALLOC(stmnt->rs1, register_alloc, struct register_rep);
	stmnt->rs1->type  = stmnt->rd->type;
	stmnt->rs1->regno = stmnt->rd->regno;

	return asm_format3(stmnt);
}

/* inc, dec, inccc, deccc synthetics 
 * opcode rd -> opcode rd,1,rd
 * opcode const13,rd -> opcode rd,const13,rd
 */
int
asm_inc_dec(struct asm_stmnt *stmnt)
{
	struct register_rep *r;

	ASM_ALLOC(r, register_alloc, struct register_rep);
	if (stmnt->rs1)
	{
		/* op rd */
		r->type = stmnt->rs1->type;
		r->regno = stmnt->rs1->regno;
		stmnt->rd = r;
		ASM_ALLOC(stmnt->immediate, int_alloc, int);
		*stmnt->immediate = 1;
	} else {
		/* op const13, rd */
		r->type = stmnt->rd->type;
		r->regno = stmnt->rd->regno;
		stmnt->rs1 = r;
	}

	return asm_format3(stmnt);
}

/* neg rs2,rd  ->  sub %g0,rs2,rd ! stmnt->rs1 has rs2 in it.
 * neg rd      ->  sub %g0,rd, rd ! stmnt->rs1 has rd in it.
 */
int
asm_neg(struct asm_stmnt *stmnt)
{
	assert(NULL != stmnt);

	if (stmnt->rd)
	{
		/* it's a 'neg rs2, rd' */
		stmnt->rs2 = stmnt->rs1;
	} else {
		/* it's a 'neg rd' */
		stmnt->rd = stmnt->rs1;
		ASM_ALLOC(stmnt->rs2, register_alloc, struct register_rep);
		stmnt->rs2->type = stmnt->rd->type;
		stmnt->rs2->regno = stmnt->rd->regno;
	}

	ASM_ALLOC(stmnt->rs1, register_alloc, struct register_rep);
	stmnt->rs1->type = REGULAR;
	stmnt->rs1->regno = 0;

	return asm_format3(stmnt);
}

/* btst reg_or_imm,rs1  ->  andcc rs1,reg_or_imm,%g0
 *
 * Gnu Assembler apparently doesn't re-arrange the operands _if_
 * they are both registers.
 */
int
asm_btst(struct asm_stmnt *stmnt)
{
	if (!stmnt->rs1)
	{
		stmnt->rs2 = stmnt->rs1;
		stmnt->rs1 = stmnt->rd;
	} else {
		/* Gnu 'as' does it this way */
		stmnt->rs2 = stmnt->rd;
	}

	ASM_ALLOC(stmnt->rd, register_alloc, struct register_rep);
	stmnt->rd->type = REGULAR;
	stmnt->rd->regno = 0;

	return asm_format3(stmnt);
}

int
asm_tst(struct asm_stmnt *stmnt)
{
	ASM_ALLOC(stmnt->rs2, register_alloc, struct register_rep);
	ASM_ALLOC(stmnt->rd, register_alloc, struct register_rep);
	stmnt->rs2->regno = stmnt->rd->regno = 0;
	stmnt->rs2->type = stmnt->rd->type = REGULAR;
	return asm_format3(stmnt);
}

int
asm_mov(struct asm_stmnt *stmnt)
{
	assert(NULL != stmnt);

	if (stmnt->rs1 && REGULAR != stmnt->rs1->type)
		return asm_rd(stmnt);

	if (stmnt->rd && REGULAR != stmnt->rd->type)
		return asm_wr(stmnt);

	stmnt->mnemonic = or_dummy;
	ASM_ALLOC(stmnt->rs2, register_alloc, struct register_rep);
	if (stmnt->rs1)
	{
		stmnt->rs2->regno = stmnt->rs1->regno;
		stmnt->rs2->type  = stmnt->rs1->type;

		stmnt->rs1->regno = REGULAR;
		stmnt->rs1->type  = 0;
	} else {
		stmnt->rs1 = stmnt->rs2;
		stmnt->rs1->type  = REGULAR;
		stmnt->rs1->regno = 0;
		stmnt->rs2 = NULL;
	}

	return asm_format3(stmnt);
}


/* assemble a "set" synthetic instruction mnemonic into a sethi
 * instruction and an or instruction as per Table A-1 of
 * SPARC v8 architecture manual */

int
asm_set(struct asm_stmnt *stmnt)
{
	int r = 0;

	assert(NULL != stmnt);

	if ((stmnt->symbol && N_ABS == (stmnt->symbol->n_type&N_TYPE)) || NULL == stmnt->symbol )
		r = asm_set_numeric(stmnt);
	else if (NULL != stmnt->symbol)
		r = asm_set_symbolic(stmnt);
	else
		internal_problem(__FILE__, __LINE__, "goofy set synthetic ");

	return r;
}

/* set LXX23,%i0 or something */
int
asm_set_symbolic(struct asm_stmnt *stmnt)
{
	unsigned int orig_imm;
	struct relocation_info *r;

	/* the %hi() part */
	stmnt->mnemonic = sethi_dummy;

	/* asm_sethi() doesn't set relocation type to RELOC_HI22 without %hi */
	if (stmnt->immediate)
	{
		orig_imm = *stmnt->immediate;
		*stmnt->immediate >>= 10;
	}

	if (stmnt->reloc)
		stmnt->reloc->r_type = RELOC_HI22;

	asm_sethi(stmnt);

	/* the %lo() part - stmnt looks like:
	 * set identifier NULL register_rd
	 * assemble  "or rd,%lo(identifier),rd" */

	stmnt->mnemonic = or_dummy;

	if (stmnt->immediate)
		*stmnt->immediate = (orig_imm & 0x3ff);

	ASM_ALLOC(stmnt->rs1, register_alloc, struct register_rep);
	stmnt->rs1->regno = stmnt->rd->regno;  /* r[1] and r[rd] the same */

	if (stmnt->reloc)
	{	/* have to put together a new struct relocation_info for
		 * the 2nd instruction of this pair */

		r = stmnt->reloc;

		STRUCT_ALLOC(stmnt->reloc, struct relocation_info);

		*stmnt->reloc = *r;
		stmnt->reloc->r_address = CURROFFSET;
		stmnt->reloc->r_type    = RELOC_LO10;
	}

	return asm_format3(stmnt);
}

int
asm_set_numeric(struct asm_stmnt *stmnt)
{
	if (-4096 <= *stmnt->immediate && 4095 >= *stmnt->immediate)
	{
		/* or %g0, value, %rd */

		stmnt->mnemonic = or_dummy;

		assert(NULL == stmnt->rs2);
		stmnt->rs1 = &reg_g0_dummy;

		asm_format3(stmnt);

		stmnt->rs1 = NULL;

	} else {

		int constant = *stmnt->immediate;

		stmnt->mnemonic = sethi_dummy;
		*stmnt->immediate = *stmnt->immediate >> 10;
		asm_sethi(stmnt);

		if (constant & 0x3ff)
		{
			/* assemble the low 10 bit part */
			stmnt->mnemonic = or_dummy;

			/* asm_format3 trims to low 13 bits - need low 10 bits */
			*stmnt->immediate = (constant & 0x3ff);

			stmnt->rs1 = stmnt->rd;

			asm_format3(stmnt);

			stmnt->rs1 = NULL;
		}
	}

	return 1;
}

int
asm_load(struct asm_stmnt *stmnt)
{
	int r;
	unsigned int old_op3;
	
	assert(NULL != stmnt);

	if (!stmnt->rs1)
	{
		/* implied %g0 */
		ASM_ALLOC(stmnt->rs1, register_alloc, struct register_rep);
		stmnt->rs1->type = REGULAR;
		stmnt->rs1->regno = 0;
	}

	if (!stmnt->rs2 && !stmnt->symbol && !stmnt->immediate)
	{
		/* implied %g0 */
		ASM_ALLOC(stmnt->rs2, register_alloc, struct register_rep);
		stmnt->rs2->type = REGULAR;
		stmnt->rs2->regno = 0;
	}

	old_op3 = stmnt->mnemonic->op3;

	if (stmnt->rd && REGULAR != stmnt->rd->type)
		switch (stmnt->rd->type)
		{
		case FP:
			/* should check for lddf, stdf: is the %frd dest fp reg evenly-numbered? */
			stmnt->mnemonic->op3 |= 0x20;
			break;
		case FSR:
			if ('l' == *stmnt->mnemonic->op_mnm)
				stmnt->mnemonic->op3 = ldfsr_dummy->op3;
			else
				stmnt->mnemonic->op3 = stfsr_dummy->op3;
			break;
		case COPROC:
			stmnt->mnemonic->op3 |= 0x30;
			break;
		case CSR:
			if ('l' == *stmnt->mnemonic->op_mnm)
				stmnt->mnemonic->op3 = ldcsr_dummy->op3;
			else
				stmnt->mnemonic->op3 = stcsr_dummy->op3;
			break;
		case FQ:
			stmnt->mnemonic = stdfq_dummy;
			break;
		case Y: case ASR: case PSR: case WIM: case TBR:
			break;
		case REGULAR:
			/* nothing */
			break;
		}

	r = asm_format3(stmnt);

	stmnt->mnemonic->op3 = old_op3;

	return r;
}

/* clr %rd -> or %g0,%g0,%rd */
int
asm_clr(struct asm_stmnt *stmnt)
{
	return asm_format3(stmnt);
}

/* clr|clrh|clrb [address]  => st %g0,[address]
 *
 * This has ugly special purpose code in it because there's no way to tell
 * a 'clr %r15' from a 'clr [%r15]' with my current grammar.  This is the only
 * instruction that has this problem, so I chose to hack around it rather than
 * fix the statement rep struct for the other 200+ opcodes
 */
int
asm_clr_mem(struct asm_stmnt *stmnt)
{
	int r;
	struct mnm *old_mnemonic;

	old_mnemonic = stmnt->mnemonic;

	if (!strcmp(stmnt->mnemonic->op_mnm, "clr"))
	{
		if (!stmnt->asi)
		{
			stmnt->rd = stmnt->rs1;
			ASM_ALLOC(stmnt->rs1, register_alloc, struct register_rep);
			ASM_ALLOC(stmnt->rs2, register_alloc, struct register_rep);

			stmnt->rs1->type = stmnt->rs2->type = REGULAR;
			stmnt->rs1->regno = stmnt->rs2->regno = 0;

			stmnt->asi = -1;  /* clr synthetic _can't_ have an ASI */

			r = asm_format3(stmnt);

			return r;

		} else
			stmnt->mnemonic = st_dummy;
	}

	ASM_ALLOC(stmnt->rd, register_alloc, struct register_rep);
	stmnt->rd->type = REGULAR;
	stmnt->rd->regno = 0;

	r = asm_load(stmnt);

	stmnt->mnemonic = old_mnemonic;

	return r;
}

/*  this is so I can use it as a place-holder */
int
real_asm_nop(void)
{
	struct format2 instn;

	instn.op = 0x0;
	instn.rd = 0x0;
	instn.op2 = 0x4;
	instn.imm22 = 0;

	write_instn((void *)&instn);

	return 1;
}

int
asm_nop(struct asm_stmnt *stmnt)
{
	return real_asm_nop();
}


int
asm_sethi(struct asm_stmnt *stmnt)
{
	struct format2 instn;

	assert(NULL != stmnt);

	instn.op  = stmnt->mnemonic->op;
	instn.op2 = stmnt->mnemonic->op2;
	instn.rd  = stmnt->rd->regno;

	if (NULL == stmnt->symbol && NULL == stmnt->immediate)
	{
		input_problem("something wrong, constant part NULL\n");
	} else {

		if (stmnt->reloc)
		{
			/* this is a little tricky: whoever calls this routine needs
			 * to set the relocation to RELOC_HI22 or RELOC_LO10.
			 * Otherwise, some assembly programmer may be counting on
			 * RELOC_22 rather than RELOC_HI22. */

			if (RELOC_UNUSED3 == stmnt->reloc->r_type)
				stmnt->reloc->r_type = RELOC_22;
			insert_relocation(__FILE__, __LINE__, stmnt->reloc, stmnt->symbol);

			instn.imm22 = 0;
		} else if (stmnt->immediate)
			instn.imm22 = *stmnt->immediate;
	}

	write_instn((int *)&instn);

	return 1;
}

int
asm_set_size(struct asm_stmnt *stmnt)
{
	int r = 4;

	if (!stmnt->symbol)
	{
		if (!stmnt->immediate)
			input_problem("set without symbol or immediate\n");
		else {
			if (-4096 <= *stmnt->immediate && 4095 >= *stmnt->immediate)
				r = 4;                            /* or %g0,value,%rd */
			else if (0 == (*stmnt->immediate & 0x3ff))
				r = 4;                            /* sethi value, %rd (no %hi)*/
			else
				r = 8;                            /* sethi; or; */
		}
	} else {
		if (N_ABS == (stmnt->symbol->n_type & N_TYPE))
			r = 4;
		else
			r = 8;    /* always a 'sethi' and an 'or' */
	}

	return r;
}

int
asm_ld2(struct asm_stmnt *stmnt)
{
	int r;
	int imm = 4, used_imm = 0;

	r = asm_load(stmnt);

	/* bump up the FP register by one */
	++stmnt->rd->regno;

	/* add a 4-byte immediate */
	if (stmnt->immediate)
		*stmnt->immediate += 4;
	else {
		stmnt->immediate = &imm;
		used_imm = 1;
	}

	if (stmnt->rs2)
	{
		ASM_DEALLOC(stmnt->rs2, register_alloc);
		stmnt->rs2 = NULL;
	}

	r += asm_load(stmnt);

	if (used_imm)
		stmnt->immediate = NULL;

	return r;
}

void
symbol_equals_expr(struct expr_node *sym, struct expr_node *expr)
{
	struct nlist *ntmp, *nsym;
	struct relocation_info *rtmp;
	int *val;
	struct register_address reg;

	assert(NULL != sym);
	assert(NULL != expr);

	if (ExprSym != sym->kind)
	{
		input_problem("symbol = expression, but symbol hasn't got a string name\n");
		return;
	}


	if (NULL == (nsym = symbol_named(sym->u.id)))
		nsym = add_symbol_named(sym->u.id);

	nsym->n_type = N_ABS;

	expr_to_imm(expr, &ntmp, &rtmp, &val, &reg);

	if (val)
	{
		nsym->n_value = *val;
		ASM_DEALLOC(val, int_alloc);
	} else
		internal_problem(__FILE__, __LINE__, "no value?\n");

	if (rtmp)
	{
		if (RELOC_UNUSED3 == rtmp->r_type)
			rtmp->r_type = RELOC_32;

		insert_relocation(__FILE__, __LINE__, rtmp, ntmp);
	}
}
