# Build a WSDL spec of the API

all: plcapi.wsdl

plcapi.wsdl:
	PYTHONPATH=../ python3 api2wsdl.py > $@

clean:
	rm -f plcapi.wsdl

.PHONY: all clean
