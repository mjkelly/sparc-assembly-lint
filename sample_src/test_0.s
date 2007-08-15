/*
 * Block comment.
 * With
 * multiple
 * lines.
 */

MYINT=10

.section ".data"
fmt: .asciz	"the number is: %d\n"

.global	main
.section ".text"		! comment
main:			! comment
	save	%sp, -96, %sp	! comment

	mov	MYINT, %l0	! comment
	mov	%g0, %l1
	add	%l0, %l1, %l2

	set	fmt, %o0
	mov	%l2, %o1
	call	printf
	nop

	ret			! comment
	restore
