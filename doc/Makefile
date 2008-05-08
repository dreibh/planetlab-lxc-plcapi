#
# (Re)builds API documentation
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

all: PLCAPI.html

.PLCAPI.xml.valid: Methods.xml

API_SOURCES = ../PLC/__init__.py ../PLC/Methods/__init__.py

Methods.xml: DocBook.py DocBookLocal.py $(API_SOURCES)
	PYTHONPATH=.. DocBookLocal.py > $@

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
	rm -f $(patsubst %,*.%,$(FORMATS)) .*.xml.valid Methods.xml

.PHONY: clean all
