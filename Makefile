run:
	./asmlint.py

clean:
	rm -f *.pyc parser.out parsetab.{py,pyc}

test:
	./testrunner.py
