/* $Id: assembler.h,v 1.7 1997/03/14 05:43:25 bediger Exp bediger $
$Log: assembler.h,v $
Revision 1.7  1997/03/14 05:43:25  bediger
minor formatting

Revision 1.6  1997/03/10 01:19:00  bediger
'tst' synthetic instruction support

Revision 1.5  1997/02/14 15:31:12  bediger
support for btst synthetic instruction

Revision 1.4  1997/02/04 03:58:04  bediger
support many more synthetic instructions

Revision 1.3  1997/01/15 01:24:56  bediger
make word-directive function back into a directive function.

Revision 1.2  1997/01/05 08:54:57  bediger
add prototype for function to assembler neg synthetic instruction

Revision 1.1  1996/12/13 14:36:37  bediger
Initial revision

*/

/* prototypes of functions that actually do the assembly */

/* include assy.h before this for definition of struct asm_stmnt */

int asm_format1(struct asm_stmnt   *stmnt);
int asm_format2(struct asm_stmnt   *stmnt);
int asm_branch(struct asm_stmnt    *stmnt);  /* struct mnm op3 used for rd */
int asm_format3(struct asm_stmnt   *stmnt);
int asm_format3c(struct asm_stmnt  *stmnt);  /* struct mnm opf used for asi */

int asm_trap(struct asm_stmnt      *stmnt);  /* struct mnm op2 used for rd */

int asm_nop(struct asm_stmnt     *stmnt);

int asm_sethi(struct asm_stmnt   *stmnt);
int asm_load(struct asm_stmnt    *stmnt);

int asm_rd(struct asm_stmnt      *stmnt);
int asm_wr(struct asm_stmnt      *stmnt);

/* synthetic instructions */
int asm_set(struct asm_stmnt     *stmnt);
int asm_mov(struct asm_stmnt     *stmnt);
int asm_cmp(struct asm_stmnt     *stmnt);
int asm_not(struct asm_stmnt     *stmnt);
int asm_neg(struct asm_stmnt     *stmnt);
int asm_jmp(struct asm_stmnt     *stmnt);
int asm_ret(struct asm_stmnt     *stmnt);
int asm_retl(struct asm_stmnt    *stmnt);
int asm_tst(struct asm_stmnt     *stmnt);
int asm_ld2(struct asm_stmnt     *stmnt);  /* ld2, st2 */
int asm_synth(struct asm_stmnt   *stmnt);  /* bset, bclr, btog */
int asm_inc_dec(struct asm_stmnt *stmnt);  /* inc, inccc, dec, decc */
int asm_clr_mem(struct asm_stmnt *stmnt);  /* clr [address], clrb, clrh */
int asm_btst(struct asm_stmnt    *stmnt);  /* btst */

int unimplemented_mnm(struct asm_stmnt     *stmnt);

int asm_set_size(struct asm_stmnt *stmnt);
