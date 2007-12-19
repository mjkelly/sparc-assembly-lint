D                       [0-9]
LD                      [1-9]
L                       [a-zA-Z_$]
H                       [a-fA-F0-9]
E                       [Ee][+-]?{D}+
FS                      (f|F|l|L)
R                       (r|R|g|G|o|O|l|L|i|I|c|C|f|F)
IS                      (u|U|l|L)*
WHITESPACE              [ \t\v\f]
%{
/*
$Log: assy.l,v $
Revision 1.12  1997/03/14 05:42:52  bediger
make it do floating point constants semi-correctly.

Revision 1.11  1997/03/10 01:17:03  bediger
add regexp for GNU "flonums"

Revision 1.10  1997/02/27 07:43:46  bediger
make '0' a legit local label

Revision 1.9  1997/02/14 06:21:34  bediger
consolidate recognition of %[pfc]sr register names, remove dead
code - assembler_dir_eol() isn't used now that directives are part
of the grammar.

Revision 1.8  1997/02/04 03:59:01  bediger
add support for goofy GCC '@function', '@object' stuff

Revision 1.7  1997/01/15 01:27:20  bediger
reflect the "directives as part of grammar" changes

Revision 1.6  1996/12/29 01:15:59  bediger
very minor changes because of cargo-cult debugging of SunOS-style
"local labels".

Revision 1.5  1996/12/19 06:51:51  bediger
add recognition of SunOS "local label"  style labels

Revision 1.4  1996/12/17 06:40:03  bediger
addition of new unary and binary arithmetic operators

Revision 1.3  1996/12/16 06:45:28  bediger
add an #include to prevent a warning

Revision 1.2  1996/12/14 19:57:07  bediger
completed changes wrt dynamic allocation of register rep structs

Revision 1.1  1996/12/12 20:49:46  bediger
Initial revision

 */

#include <string.h>
#include <assert.h>
#include <ctype.h>     /* isprint() prototype */
#include <stdlib.h>    /* required by shortcut_alloc.h */
#include <sys/param.h> /* MAXPATHLEN */
#include <a.out.h>     /* for inclusion of expr.h */

#include <assy.h>
#include <expr.h>            /* y.tab.h needs this first */
#include <shortcut_alloc.h>  /* ASM_ALLOC() and struct mem_stack */

extern int pass;     /* pass 1 or pass 2 */

#ifdef USE_DMALLOC
#include <dmalloc.h>
#endif

#include "y.tab.h"

void found_nonstandard(void);
void comment(void);
void eol_comment(void);
int extract_line_number(char *string);
char *extract_file_name(char *string);

#ifndef TRUE
#define TRUE 1
#endif
#ifndef FALSE
#define FALSE 0
#endif

static char rcsident[] = "$Header: /home/ediger/src/csrc/sparc_assembler10/RCS/assy.l,v 1.12 1997/03/14 05:42:52 bediger Exp bediger $";

extern struct mem_stack register_alloc;
%}

%%
"/*"                    { comment();   /* Read in rest of comment. */ }

"!"						{ eol_comment(); return TK_EOSTMNT; }

0[xX]{H}+{IS}?          {
		yylval.val = (unsigned int)strtoul(yytext, NULL, 0x10);
		return INTEGER_CONSTANT;
	}
0{D}+{IS}?              {
		yylval.val = (unsigned int)strtoul(yytext, NULL, 010);
		return INTEGER_CONSTANT;
	}
{D}+{IS}?               {
		yylval.val = (unsigned int)strtoul(yytext, NULL, 10);
		return INTEGER_CONSTANT;
	}
'(\\.|[^\\'])+'         {
		yylval.val = (unsigned int)yytext[1];
		return INTEGER_CONSTANT;
	}

0[a-zA-Z][+-]*({D}+|({D}*(\.{D}*)+))([Ee][+-]*{D}*)* {
		/* GNU GAS 2.3 format for "flonum". */
		yylval.dbl_val = strtod(&yytext[2], NULL);
		return(FLOATING_CONSTANT);
}

{D}+{E}{FS}?			{
		yylval.dbl_val = strtod(&yytext[0], NULL);
		return(FLOATING_CONSTANT);
	}
{D}*"."{D}+({E})?{FS}?	{
		yylval.dbl_val = strtod(&yytext[0], NULL);
		return(FLOATING_CONSTANT);
	}
{D}+"."{D}*({E})?{FS}?	{
		yylval.dbl_val = strtod(&yytext[0], NULL);
		return(FLOATING_CONSTANT);
	}

"%hi" {return TK_HI;}
"%lo" {return TK_LO;}

"%"{R}{D}+ {
		ASM_ALLOC(yylval.reg, register_alloc, struct register_rep);

		yylval.reg->type = REGULAR;
		yylval.reg->regno = atoi(&yytext[2]);

		switch (yytext[1])
		{
		case 'o': case 'O': yylval.reg->regno +=  8; break;
		case 'l': case 'L': yylval.reg->regno += 16; break;
		case 'i': case 'I': yylval.reg->regno += 24; break;
		case 'c': case 'C': yylval.reg->type = COPROC; break;
		case 'f': case 'F': yylval.reg->type = FP; break;
		default:
			break;
		}

		return REGISTER_NAME;
	}

"%sp" {
		ASM_ALLOC(yylval.reg, register_alloc, struct register_rep);

		yylval.reg->type = REGULAR;
		yylval.reg->regno = 14;
		return REGISTER_NAME;
	}
"%fp" {
		ASM_ALLOC(yylval.reg, register_alloc, struct register_rep);

		yylval.reg->type = REGULAR;
		yylval.reg->regno = 30;
		return REGISTER_NAME;
	}
"%y" {
		ASM_ALLOC(yylval.reg, register_alloc, struct register_rep);
		yylval.reg->type = Y;
		return REGISTER_NAME;
	}
"%wim" {

		ASM_ALLOC(yylval.reg, register_alloc, struct register_rep);
		yylval.reg->type = WIM;
		return REGISTER_NAME;
	}
%asr{D}+ {
		ASM_ALLOC(yylval.reg, register_alloc, struct register_rep);
		yylval.reg->type = ASR;
		yylval.reg->regno = atoi(&yytext[4]);
		return REGISTER_NAME;
	}
%[pfc]sr {
		ASM_ALLOC(yylval.reg, register_alloc, struct register_rep);
		yylval.reg->regno = 0;
		switch (yytext[1])
		{
		case 'p': yylval.reg->type = PSR; break;
		case 'f': yylval.reg->type = FSR; break;
		case 'c': yylval.reg->type = CSR; break;
		}
		return REGISTER_NAME;
	}
%fq {
		ASM_ALLOC(yylval.reg, register_alloc, struct register_rep);
		yylval.reg->regno = 0;
		yylval.reg->type = FQ;
		return REGISTER_NAME;
}
%cq {
		input_problem("Doesn't currently handle %s registers: they're implementation dependent\n", yytext);
		ASM_ALLOC(yylval.reg, register_alloc, struct register_rep);
		yylval.reg->regno = 0;
		yylval.reg->type = REGULAR;
		return REGISTER_NAME;
}

"%tbr" {
		ASM_ALLOC(yylval.reg, register_alloc, struct register_rep);
		yylval.reg->type = TBR;
		return REGISTER_NAME;
	}

@{L}({L}|{D}|\.)*           {
		/* GCC 2.x puts out some goofy directives that have '@function'
		 * or '@object' in them. */
		yylval.string = strcpy(malloc(strlen(yytext)+1), yytext);
		return IDENTIFIER;
	}

{L}({L}|{D}|\.)*           {
		struct mnm *p;
		p = is_mnemonic(yytext);
		if (NULL != p)
		{
			yylval.mnemonic = p;
			return MNEMONIC;
		} else {
			/* strcpy instead of strdup to allow malloc-debugging
			 * packages to #define their new calls */
			yylval.string = strcpy(malloc(strlen(yytext)+1), yytext);
			return IDENTIFIER;
		}
	}

\.*{L}({L}|{D}|\.)*           {
		struct bzx *p;
		if (NULL != (p = assembler_directive(yytext)))
		{
			yylval.directive = p;
			return DIRECTIVE;
		} else {
			struct mnm *m = is_mnemonic(yytext);

			if (NULL != m)
			{
				yylval.mnemonic = m;
				return MNEMONIC;
			} else {
				yylval.string = strcpy(malloc(strlen(yytext)+1), yytext);
				return IDENTIFIER;
			}
		}
	}

\"(\\.|[^\\"])*\"  {
		int l = strlen(yytext);

		/* ditch the double-quotes */
		yylval.string = malloc(l);
		strcpy(yylval.string, yytext+1);
		yylval.string[l-2] = '\0';
		return(STRING_CONSTANT);
	}

[0-9][bf]  {
		yylval.string = strcpy(malloc(strlen(yytext)+1), yytext);
		return IDENTIFIER;
	}

";"                     {  return(TK_EOSTMNT); }
","                     {  return(TK_COMMA); }
"="                     {  return(TK_EQUALS); }
":"                     {  return(TK_COLON); }
"("                     {  return(TK_LPAREN); }
")"                     {  return(TK_RPAREN); }
"["                     {  return(TK_LBRACK); }
"]"                     {  return(TK_RBRACK); }
"+"                     {  return(TK_PLUS); }
"-"                     {  return(TK_MINUS); }
"/"                     {  return(TK_SLASH); }
"*"                     {  return(TK_STAR); }
"%"                     {  return(TK_MODULO); }
"|"                     {  return(TK_BIT_OR); }
"&"                     {  return(TK_BIT_AND); }
"^"                     {  return(TK_BIT_XOR); }
"~"                     {  return(TK_TILDE); }
">>"                    {  return(TK_RIGHT_SHIFT); }
"<<"                    {  return(TK_LEFT_SHIFT); }
{WHITESPACE}            {  ; /* Absorb whitespace character. */ }

^{WHITESPACE}*#[ \t]*("line"[ \t]+)?{D}+([ \t]+\"[^"\n]*\")?.*  {
	char *fname;

	lineno = extract_line_number(yytext) - 1;

	if (NULL != (fname = extract_file_name(yytext)))
		working_input_file = fname;
		
}

\n                      { ++lineno; return TK_EOSTMNT; }

.                       {  /* Trap any non-standard characters. */
                            found_nonstandard(); }

%%
int
extract_line_number(char *string)
{
	return (unsigned)strtol(&string[strcspn(string, "0123456789")], NULL, 10);
}
 
char working_file_buf[MAXPATHLEN];

char *
extract_file_name(char *string)
{
   char *begin;

   /* File name is enclosed in quotes. Return NULL if no first quote. */
   begin = strchr(string, '"');
   if (begin != NULL)
   {
      char *end;

      ++begin;      /* Skip past first quote. */

      /* If no trailing quote, return NULL. */
      end = strchr(begin, '"');
      if (end == NULL)
         begin = NULL;
      else
      {
         int l = (int)((unsigned)end - (unsigned)begin);

         strncpy(working_file_buf, begin, l);
         working_file_buf[l] = '\0';

         begin = working_file_buf;
      }
   }

   return begin;
}
void
comment(void)
{
	int c;

	/* Loop until input exhausted or end-of-comment reached. */
	for ( ; (c = input()) != '\0'; )
	{
		if ('*' == c)                    /* Could be end-of-comment. */
		{
			int c1;
			
			if ((c1 = input()) == '/')
				break;                     /* Is end-of-comment. */
			else
				unput(c1);                 /* False alarm. Not end-of-comment. */
		}

		if ('\n' == c)
			++lineno;
	}
	
}

void
eol_comment(void)
{
	int c;

	/* Loop until input exhausted or end-of-comment reached. */
	for ( ; (c = input()) != '\0'; )
	{
		if ('\n' == c)
		{
			++lineno;
			break;
		}
	}
	
}

void
found_nonstandard(void)
{
	extern int lineno;

	if (isprint(yytext[0]))
		fprintf(stderr, "found non-standard character 0x%x ('%c') at line %d in \"%s\"\n",
			yytext[0], yytext[0], lineno, working_input_file);
	else
		fprintf(stderr, "found non-standard character 0x%x at line %d in \"%s\"\n",
			yytext[0], lineno, working_input_file);
}
