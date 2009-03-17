#
# (Re)builds API documentation
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

all: PLCAPI.html

# XML - as opposed to SGML - requires an identifier - see 
# http://www.docbook.org/tdg/en/html/appb.html
# and, openjade opens http connections when using the official URL 
# as an identifier; this is slow, and sometimes fails and breaks the build

# locating locally installed docbook43 dtd - fedora-specific
remote-docbook-43 = http://www.oasis-open.org/docbook/xml/4.3/docbookx.dtd
local-docbook-43 = $(wildcard /usr/share/sgml/docbook/xml-dtd-4.3-*/docbookx.dtd)
docbook-43=$(if $(local-docbook-43),$(local-docbook-43),$(remote-docbook-43))

PLCAPI.xml: PLCAPI.xml.in
	$(if $(local-docbook-43), \
	echo Using locally installed DTD $(local-docbook-43), \
	echo WARNING - could not locate local DTD - using remote $(remote-docbook-43))
	sed -e "s:@DOCBOOK-43@:$(docbook-43):" $< > $@

.PLCAPI.xml.valid: Methods.xml

API_SOURCES = ../PLC/__init__.py ../PLC/Methods/__init__.py

Methods.xml: DocBook.py DocBookLocal.py $(API_SOURCES)
	PYTHONPATH=.. ./DocBookLocal.py > $@

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
