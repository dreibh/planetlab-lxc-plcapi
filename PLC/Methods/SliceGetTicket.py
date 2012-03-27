import os
import sys
from subprocess import Popen, PIPE, call
from tempfile import NamedTemporaryFile
from xml.sax.saxutils import escape, quoteattr, XMLGenerator

from PLC.Faults import *
from PLC.Slices import Slice, Slices
from PLC.Nodes import Node, Nodes
from PLC.Persons import Person, Persons
from PLC.SliceTags import SliceTag, SliceTags

from PLC.Methods.GetSliceTicket import GetSliceTicket

class PrettyXMLGenerator(XMLGenerator):
    """
    Adds indentation to the beginning and newlines to the end of
    opening and closing tags.
    """

    def __init__(self, out = sys.stdout, encoding = "utf-8", indent = "", addindent = "", newl = ""):
        XMLGenerator.__init__(self, out, encoding)
        # XMLGenerator does not export _write()
        self.write = self.ignorableWhitespace
        self.indents = [indent]
        self.addindent = addindent
        self.newl = newl

    def startDocument(self):
        XMLGenerator.startDocument(self)

    def startElement(self, name, attrs, indent = True, newl = True):
        if indent:
            self.ignorableWhitespace("".join(self.indents))
        self.indents.append(self.addindent)

        XMLGenerator.startElement(self, name, attrs)

        if newl:
            self.ignorableWhitespace(self.newl)

    def characters(self, content):
        # " to &quot;
        # ' to &apos;
        self.write(escape(content, {
            '"': '&quot;',
            "'": '&apos;',
            }))

    def endElement(self, name, indent = True, newl = True):
        self.indents.pop()
        if indent:
            self.ignorableWhitespace("".join(self.indents))

        XMLGenerator.endElement(self, name)

        if newl:
            self.ignorableWhitespace(self.newl)

    def simpleElement(self, name, attrs = {}, indent = True, newl = True):
        if indent:
            self.ignorableWhitespace("".join(self.indents))

        self.write('<' + name)
        for (name, value) in attrs.items():
            self.write(' %s=%s' % (name, quoteattr(value)))
        self.write('/>')

        if newl:
            self.ignorableWhitespace(self.newl)

class SliceGetTicket(GetSliceTicket):
    """
    Deprecated. See GetSliceTicket.

    Warning: This function exists solely for backward compatibility
    with the old public PlanetLab 3.0 Node Manager, which will be
    removed from service by 2007. This call is not intended to be used
    by any other PLC except the public PlanetLab.
    """

    status = "deprecated"

    def call(self, auth, slice_id_or_name):
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice"
        slice = slices[0]

        # Allow peers to obtain tickets for their own slices
        if slice['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local slice"

        if slice['instantiation'] != 'delegated':
            raise PLCInvalidArgument, "Not in delegated state"

        nodes = Nodes(self.api, slice['node_ids']).dict()
        persons = Persons(self.api, slice['person_ids']).dict()
        slice_tags = SliceTags(self.api, slice['slice_tag_ids']).dict()

        ticket = NamedTemporaryFile()

        xml = PrettyXMLGenerator(out = ticket, encoding = self.api.encoding, indent = "", addindent = "  ", newl = "\n")
        xml.startDocument()

        # <ticket>
        xml.startElement('ticket', {})

        # <slice name="site_slice" id="12345" expiry="1138712648">
        xml.startElement('slice',
                         {'id': str(slice['slice_id']),
                          'name': unicode(slice['name']),
                          'expiry': unicode(int(slice['expires']))})

        # <nodes>
        xml.startElement('nodes', {})
        for node_id in slice['node_ids']:
            if not nodes.has_key(node_id):
                continue
            node = nodes[node_id]
            # <node id="12345" hostname="node.site.domain"/>
            xml.simpleElement('node',
                              {'id': str(node['node_id']),
                               'hostname': unicode(node['hostname'])})
        # </nodes>
        xml.endElement('nodes')

        # <users>
        xml.startElement('users', {})
        for person_id in slice['person_ids']:
            if not persons.has_key(person_id):
                continue
            user = persons[person_id]
            # <user person_id="12345" email="user@site.domain"/>
            xml.simpleElement('user',
                              {'person_id': unicode(user['person_id']),
                               'email': unicode(user['email'])})
        # </users>
        xml.endElement('users')

        # <rspec>
        xml.startElement('rspec', {})
        for slice_tag_id in slice['slice_tag_ids']:
            if not slice_tags.has_key(slice_tag_id):
                continue
            slice_tag = slice_tags[slice_tag_id]

            name = slice_tag['name']
            value = slice_tag['value']

            def kbps_to_bps(kbps):
                bps = int(kbps) * 1000
                return bps

            def max_kbyte_to_bps(max_kbyte):
                bps = int(max_kbyte) * 1000 * 8 / 24 / 60 / 60
                return bps

            # XXX Used to support multiple named values for each attribute type
            name_type_cast = {
                'cpu_share': ('nm_cpu_share', 'cpu_share', 'integer', int),

                'net_share': ('nm_net_share', 'rate', 'integer', int),
                'net_min_rate': ('nm_net_min_rate', 'rate', 'integer', int),
                'net_max_rate': ('nm_net_max_rate', 'rate', 'integer', int),
                'net_max_kbyte': ('nm_net_avg_rate', 'rate', 'integer', max_kbyte_to_bps),

                'net_i2_share': ('nm_net_exempt_share', 'rate', 'integer', int),
                'net_i2_min_rate': ('nm_net_exempt_min_rate', 'rate', 'integer', kbps_to_bps),
                'net_i2_max_rate': ('nm_net_exempt_max_rate', 'rate', 'integer', kbps_to_bps),
                'net_i2_max_kbyte': ('nm_net_exempt_avg_rate', 'rate', 'integer', max_kbyte_to_bps),

                'disk_max': ('nm_disk_quota', 'quota', 'integer', int),
                'plc_agent_version': ('plc_agent_version', 'version', 'string', str),
                'plc_slice_type': ('plc_slice_type', 'type', 'string', str),
                'plc_ticket_pubkey': ('plc_ticket_pubkey', 'key', 'string', str),
                }

            if name == 'initscript':
                (attribute_name, value_name, type) = ('initscript', 'initscript_id', 'integer')
                value = slice_tag['slice_tag_id']
            elif name in name_type_cast:
                (attribute_name, value_name, type, cast) = name_type_cast[name]
                value = cast(value)
            else:
                attribute_name = value_name = name
                type = "string"

            # <resource name="tag_type">
            xml.startElement('resource', {'name': unicode(attribute_name)})

            # <value name="element_name" type="element_type">
            xml.startElement('value',
                             {'name': unicode(value_name),
                              'type': type},
                             newl = False)
            # element value
            xml.characters(unicode(value))
            # </value>
            xml.endElement('value', indent = False)

            # </resource>
            xml.endElement('resource')
        # </rspec>
        xml.endElement('rspec')

        # </slice>
        xml.endElement('slice')

        # Add signature template
        xml.startElement('Signature', {'xmlns': "http://www.w3.org/2000/09/xmldsig#"})
        xml.startElement('SignedInfo', {})
        xml.simpleElement('CanonicalizationMethod', {'Algorithm': "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"})
        xml.simpleElement('SignatureMethod', {'Algorithm': "http://www.w3.org/2000/09/xmldsig#rsa-sha1"})
        xml.startElement('Reference', {'URI': ""})
        xml.startElement('Transforms', {})
        xml.simpleElement('Transform', {'Algorithm': "http://www.w3.org/2000/09/xmldsig#enveloped-signature"})
        xml.endElement('Transforms')
        xml.simpleElement('DigestMethod', {'Algorithm': "http://www.w3.org/2000/09/xmldsig#sha1"})
        xml.simpleElement('DigestValue', {})
        xml.endElement('Reference')
        xml.endElement('SignedInfo')
        xml.simpleElement('SignatureValue', {})
        xml.endElement('Signature')

        xml.endElement('ticket')
        xml.endDocument()

        if not hasattr(self.api.config, 'PLC_API_TICKET_KEY') or \
           not os.path.exists(self.api.config.PLC_API_TICKET_KEY):
            raise PLCAPIError, "Slice ticket signing key not found"

        ticket.flush()

        # Sign the ticket
        p = Popen(["xmlsec1", "--sign",
                   "--privkey-pem", self.api.config.PLC_API_TICKET_KEY,
                   ticket.name],
                  stdin = PIPE, stdout = PIPE, stderr = PIPE, close_fds = True)
        signed_ticket = p.stdout.read()
        err = p.stderr.read()
        rc = p.wait()

        ticket.close()

        if rc:
            raise PLCAPIError, err

        return signed_ticket
