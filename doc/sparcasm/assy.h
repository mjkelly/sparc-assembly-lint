/*
 * Requires stdio.h, stdlib.h, assert.h be included first
 */

/* $Header: /home/ediger/src/csrc/sparc_assembler10/RCS/assy.h,v 1.5 1997/03/14 05:43:25 bediger Exp bediger $
$Log: assy.h,v $
Revision 1.5  1997/03/14 05:43:25  bediger
minor formatting

Revision 1.4  1997/02/04 03:58:32  bediger
new assembly statement representation

Revision 1.3  1997/01/15 01:26:36  bediger
reflect the "directives as part of grammar" changes

Revision 1.2  1996/12/29 01:15:33  bediger
support for cmd-line specification of symbol table debugging

Revision 1.1  1996/12/12 21:03:21  bediger
Initial revision

*/

#define STRUCT_ALLOC(x, type) assert(NULL!=((x)=(type*)malloc(sizeof*(x))))

enum register_type { REGULAR, FP, COPROC, Y, ASR, PSR, WIM, TBR, FSR, CSR, FQ };

/* for some values of the field named "type", the field named "regno" is
 * meaningless: there is only one %y, %wim, %tbr or %psr register.  */

struct register_rep {
	enum register_type type;
	int regno;
};

struct register_address {
	struct register_rep *reg1;
	struct register_rep *reg2;
};

struct asm_stmnt {
	struct mnm             *mnemonic;
	struct register_rep    *rs1;
	struct register_rep    *rs2;
	struct register_rep    *rd;
	struct nlist           *symbol;
	struct relocation_info *reloc;
	int                    *immediate;
	int                     asi;
};

struct expr_list_node {
	struct expr_node      *expression;
	struct expr_list_node *next;
};

struct expr_list {
	struct bzx            *directive;
	struct expr_list_node *tail;
	struct expr_list_node *head;
};

/* These structs need to be known to mnemonic and assembler directive
 * lookup, to the lexer, so it can call the assembler directive
 * function, and to the parser, so it can call the assembly function.
 *
 * struct bzx's are associated with assembler directives, struct mnm's
 * with op-code mnemonics.  member field used for lookup, fp field to
 * perform assembly or do the assembler directive action.
 */

struct bzx {
	char * const directive;
	int (* const fp)(char *, struct expr_list_node *);
	const int p1sz;
	int (* const size_fn)(char *, struct expr_list_node *);
};

struct mnm {
	char * const op_mnm;

	int (* const asm_fn)(struct asm_stmnt *);

	const unsigned char op;
	const unsigned char op2;
	      unsigned char op3;   /* branches (reg, fp, cp) use as 'cond' */
	const unsigned short opf;

	unsigned char anul_bit;  /* parser writes to this field */
};

/* op3 field of struct mnm gets used several different ways:
 * as the op3 field of format 3a and 3b instructions - the instructions that use
 *      3 addresses: 3 registers, or 3 regs and an immediate.  This allows
 *      the use of a single routine (asm_3addr()) to do the construction
 *      of all format 3a/3b instructions.
 * as the "cond" field of a branch instruction (rd field of format 2a)
 * as the op3 field for loads and stores - distinguish between ld, ldb, ldd, etc
 * as the entire, pre-encoded instruction in 2 cases: ret and retl pseudo-ops
 */

struct mnm *is_mnemonic(char *s);
struct bzx *assembler_directive(char *s);
int         bzx_cmp(const void *key, const void *array_member);
int         mnm_cmp(const void *key, const void *array_member);

struct asm_stmnt *
construct_stmnt(
	struct mnm       *mnemonic,
	struct expr_node *r1,
	struct expr_node *r2,
	struct expr_node *r3,
	struct expr_node *asi
);

void free_stmnt(struct asm_stmnt *p);

void symbol_equals_expr(struct expr_node *sym, struct expr_node *expr);

enum CurrentSegment {TEXT_SEG = 0, DATA_SEG = 1};

#define CURSEGNAME ((TEXT_SEG==current_segment)?"text":"data")
#define CURROFFSET (outs_offset[current_segment])
/*#define CURRSEG    (outs[current_segment])*/

extern int outs_offset[], bss_offset, lineno, sym_debug, offset_debug;
extern char *working_input_file;
extern enum CurrentSegment current_segment;
extern FILE *a_out;
