#
# Build xmlrpc.so PHP extension
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

CC := gcc
CFLAGS := -g -O2 -I. -Ilibxmlrpc -fPIC
CFLAGS += $(shell php-config --includes)
CFLAGS += $(shell xml2-config --cflags)

LDFLAGS := -shared --export-dynamic
LIBS := -lexpat

# for building on fedora 8
ifneq "$(shell ld --help | grep build-id)" ""
#not needed# CFLAGS += -Wl,--build-id
LD += --build-id
endif

all: xmlrpc.so

xmlrpc.so: xmlrpc-epi-php.o $(patsubst %.c, %.o, $(wildcard libxmlrpc/*.c))
	$(LD) $(LDFLAGS) -o $@ $^ $(LIBS)

clean:
	rm -f *.o libxmlrpc/*.o *.so

.PHONY: all clean
