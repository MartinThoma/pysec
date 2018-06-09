upload:
	make clean
	python3 setup.py sdist bdist_wheel && twine upload dist/*

test:
	nosetests --with-coverage --cover-erase --cover-package pysec --logging-level=INFO --cover-html

testall:
	make test
	cheesecake_index -n pysec -v

count:
	cloc . --exclude-dir=docs,cover,dist,pysec.egg-info

countc:
	cloc . --exclude-dir=docs,cover,dist,pysec.egg-info,tests

countt:
	cloc tests

clean:
	rm -f *.hdf5 *.yml *.csv