# Build a WSDL spec of the API

all: plc_api.wsdl

plc_api.wsdl:
	./api2wsdl.py -o plc_api.wsdl

clean:
	rm -f plc_api.wsdl

.PHONY: all clean
