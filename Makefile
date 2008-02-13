INSTALLFILE = \
	DATAREAD/srcIndices/Makefile.DEPEND \
	EMPIRICAL/srcIE/Makefile.DEPEND

install:
	touch ${INSTALLFILE}

clean:
	touch ${INSTALLFILE}
	cd NOMPI/src;                 make clean
	cd TIMING/src;                make clean
	cd TIMING/srcEmpty;           make clean
	cd TIMING/doc;                make clean
	cd DATAREAD/srcIndices;       make clean
	cd DATAREAD/srcMagnetogram;   make clean
	cd EMPIRICAL/srcIE;           make clean
	cd EMPIRICAL/srcGM;           make clean
	cd EMPIRICAL/srcUA;           make clean  

distclean:
	touch ${INSTALLFILE}
	cd NOMPI/src;                 make distclean
	cd TIMING/src;                make distclean
	cd TIMING/srcEmpty;           make distclean
	cd TIMING/doc;                make distclean
	cd DATAREAD/srcIndices;       make distclean
	cd DATAREAD/srcMagnetogram;   make distclean
	cd EMPIRICAL/srcIE;           make distclean
	cd EMPIRICAL/srcGM;           make distclean
	cd EMPIRICAL/srcUA;           make distclean
	rm -f *~

dist: distclean
	rm -f ${INSTALLFILE}
	/bin/tar -cf util.tar .
