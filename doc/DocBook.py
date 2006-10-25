#!/usr/bin/python
#
# Generates a DocBook section documenting all PLCAPI methods on
# stdout.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: DocBook.py,v 1.2 2006/10/25 14:32:01 mlhuang Exp $
#

import xml.dom.minidom
from xml.dom.minidom import Element, Text
import codecs

from PLC.API import PLCAPI
from PLC.Method import *

api = PLCAPI(None)

# xml.dom.minidom.Text.writexml adds surrounding whitespace to textual
# data when pretty-printing. Override this behavior.
class TrimText(Text):
    def writexml(self, writer, indent="", addindent="", newl=""):
        Text.writexml(self, writer, "", "", "")

class TrimTextElement(Element):
    def writexml(self, writer, indent="", addindent="", newl=""):
        writer.write(indent)
        Element.writexml(self, writer, "", "", "")
        writer.write(newl)

class simpleElement(TrimTextElement):
    """<tagName>text</tagName>"""
    def __init__(self, tagName, text = None):
        TrimTextElement.__init__(self, tagName)
        if text is not None:
            t = TrimText()
            t.data = unicode(text)
            self.appendChild(t)

class paraElement(simpleElement):
    """<para>text</para>"""
    def __init__(self, text = None):
        simpleElement.__init__(self, 'para', text)

class blockquoteElement(Element):
    """<blockquote><para>text...</para><para>...text</para></blockquote>"""
    def __init__(self, text = None):
        Element.__init__(self, 'blockquote')
        if text is not None:
            # Split on blank lines
            lines = [line.strip() for line in text.strip().split("\n")]
            lines = "\n".join(lines)
            paragraphs = lines.split("\n\n")

            for paragraph in paragraphs:
                self.appendChild(paraElement(paragraph))

class entryElement(simpleElement):
    """<entry>text</entry>"""
    def __init__(self, text = None):
        simpleElement.__init__(self, 'entry', text)

class rowElement(Element):
    """
    <row>
      <entry>entries[0]</entry>
      <entry>entries[1]</entry>
      ...
    </row>
    """

    def __init__(self, entries = None):
        Element.__init__(self, 'row')
        if entries:
            for entry in entries:
                if isinstance(entry, entryElement):
                    self.appendChild(entry)
                else:
                    self.appendChild(entryElement(entry))

class informaltableElement(Element):
    """
    <informaltable>
      <tgroup>
	<thead>
	  <row>
	    <entry>label1</entry>
	    <entry>label2</entry>
	    ...
	  </row>
	</thead>
	<tbody>
	  <row>
	    <entry>row1value1</entry>
	    <entry>row1value2</entry>
	    ...
	  </row>
	  ...
	</tbody>
      </tgroup>
    </informaltable>
    """

    def __init__(self, head = None, rows = None):
        Element.__init__(self, 'informaltable')
        tgroup = Element('tgroup')
        self.appendChild(tgroup)
        if head:
            thead = Element('thead')
            tgroup.appendChild(thead)
            if isinstance(head, rowElement):
                thead.appendChild(head)
            else:
                thead.appendChild(rowElement(head))
        if rows:
            tbody = Element('tbody')
            tgroup.appendChild(tbody)
            for row in rows:
                if isinstance(row, rowElement):
                    tbody.appendChild(row)
                else:
                    tobdy.appendChild(rowElement(row))
            cols = len(thead.childNodes[0].childNodes)
            tgroup.setAttribute('cols', str(cols))

def parameters(param, name, optional, doc, indent, step):
    """Format a parameter into parameter row(s)."""

    rows = []

    row = rowElement()
    rows.append(row)

    # Parameter name
    entry = entryElement()
    entry.appendChild(simpleElement('literallayout', indent + name))
    row.appendChild(entry)

    # Parameter type
    param_type = python_type(param)
    row.appendChild(entryElement(xmlrpc_type(param_type)))

    # Whether parameter is optional
    if optional is not None:
        row.appendChild(entryElement(str(bool(optional))))
    else:
        row.appendChild(entryElement(""))

    # Parameter documentation
    row.appendChild(entryElement(doc))

    # Indent the name of each sub-parameter
    subparams = []
    if isinstance(param, dict):
        subparams = param.iteritems()
    elif isinstance(param, Mixed):
        subparams = [(name, subparam) for subparam in param]
    elif isinstance(param, (list, tuple)):
        subparams = [("", subparam) for subparam in param]

    for name, subparam in subparams:
        if isinstance(subparam, Parameter):
            (optional, doc) = (subparam.optional, subparam.doc)
        else:
            (optional, doc) = (None, "")
        rows += parameters(subparam, name, optional, doc, indent + step, step)

    return rows

for method in api.methods:
    func = api.callable(method)
    (min_args, max_args, defaults) = func.args()

    section = Element('section')
    section.setAttribute('id', func.name)
    section.appendChild(simpleElement('title', func.name))

    para = paraElement('Status:')
    para.appendChild(blockquoteElement(func.status))
    section.appendChild(para)

    prototype = "%s (%s)" % (method, ", ".join(max_args))
    para = paraElement('Prototype:')
    para.appendChild(blockquoteElement(prototype))
    section.appendChild(para)

    para = paraElement('Description:')
    para.appendChild(blockquoteElement(func.__doc__))
    section.appendChild(para)

    para = paraElement('Parameters:')
    blockquote = blockquoteElement()
    para.appendChild(blockquote)
    section.appendChild(para)

    head = rowElement(['Name', 'Type', 'Optional', 'Description'])
    rows = []

    indent = "  "
    for name, param, default in zip(max_args, func.accepts, defaults):
        optional = name not in min_args
        if isinstance(param, Parameter):
            doc = param.doc
        else:
            doc = ""
        rows += parameters(param, name, optional, doc, "", indent)

    if rows:
        informaltable = informaltableElement(head, rows)
        informaltable.setAttribute('frame', "none")
        informaltable.setAttribute('rules', "rows")
        blockquote.appendChild(informaltable)
    else:
        blockquote.appendChild(paraElement("None"))

    para = paraElement('Returns:')
    blockquote = blockquoteElement()
    para.appendChild(blockquote)
    section.appendChild(para)

    head = rowElement(['Name', 'Type', 'Optional', 'Description'])
    if isinstance(func.returns, Parameter):
        doc = func.returns.doc
    else:
        doc = ""
    indent = "  "
    rows = parameters(func.returns, "", None, doc, "", indent)
    informaltable = informaltableElement(head, rows)
    informaltable.setAttribute('frame', "none")
    informaltable.setAttribute('rules', "rows")
    blockquote.appendChild(informaltable)

    print section.toprettyxml(encoding = "UTF-8")
