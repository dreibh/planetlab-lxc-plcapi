#
# (Re)builds API documentation
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Makefile,v 1.1 2006/09/06 15:34:41 mlhuang Exp $
#

all: PLCAPI.pdf

.PLCAPI.xml.valid: Methods.xml

Methods.xml: DocBook.py ../PLC/__init__.py ../PLC/Methods/__init__.py
	PYTHONPATH=.. python $< > $@

#
# Documentation
#

# Validate the XML
.%.xml.valid: %.xml
	xmllint --valid --output $@ $<

# Remove the temporary output file after compilation
.SECONDARY: .%.xml.valid

# Compile it into other formats
FORMATS := dvi html man ps pdf rtf tex texi txt

DOCBOOK2FLAGS := -V biblio-number=1

define docbook2
%.$(1): %.xml .%.xml.valid
	docbook2$(1) --nochunks $$(DOCBOOK2FLAGS) $$<
endef

$(foreach format,$(FORMATS),$(eval $(call docbook2,$(format))))

clean:
	rm -f $(patsubst %,*.%,$(FORMATS)) .*.xml.valid

docclean:
	rm -f Methods.xml PLCAPI.pdf

force:

.PHONY: force clean docclean
