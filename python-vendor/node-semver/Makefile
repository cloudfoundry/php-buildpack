DST=README.rst
default:
	echo semver > ${DST}
	echo ================= >> ${DST}
	echo "" >> ${DST}
	echo "python version of [node-semver](https://github.com/isaacs/node-semver)" >> ${DST}
	echo "" >> ${DST}
	echo ".. code:: python\n" >> ${DST}
	cat ./demo.py | gsed 's/^\(.\)/   \1/g' >> ${DST}
