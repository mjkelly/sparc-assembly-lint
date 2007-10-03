foo:
	save	%sp, -96, %sp
	save	%sp, -(92 + 4 + 2) & -8, %sp
	save	%sp, -(92 + STACK_OFFSET) & -8, %sp
