/*
 * structs representing SPARC 32 bit instruction formats.
 * These may or may not be portable, because they depend
 * heavily on how the compiler represents bit fields.
 *
 * This is all per version 8 of The SPARC Architecture
 * Reference Manual.
 * $Id: formats.h,v 1.1 1996/12/13 14:36:37 bediger Exp bediger $
 * $Log: formats.h,v $
 * Revision 1.1  1996/12/13 14:36:37  bediger
 * Initial revision
 *
 * Revision 1.1  1993/12/17  00:01:14  bediger
 * Initial revision
 *
 */

/* call and link instruction */
struct format1 {
	unsigned int op:2;
	unsigned int disp30:30;
};

/* sethi and branches */
struct format2 {
	unsigned int op:2;
	unsigned int rd:5;  /* annul bit carried around in rd */
	unsigned int op2:3;
	unsigned int imm22:22;
};

/* memory, arithmetic, logical and shifts */
struct format3a {
	unsigned int op:2;
	unsigned int rd:5;
	unsigned int op3:6;
	unsigned int rs1:5;
	unsigned int i:1;
	unsigned int asi:8;
	unsigned int rs2:5;
};

struct format3b {
	unsigned int op:2;
	unsigned int rd:5;
	unsigned int op3:6;
	unsigned int rs1:5;
	unsigned int i:1;
	unsigned int simm13:13;
};


/* floating point ops */
struct format3c {
	unsigned int op:2;
	unsigned int rd:5;
	unsigned int op3:6;
	unsigned int rs1:5;
	unsigned int opf:9;
	unsigned int rs2:5;
};
