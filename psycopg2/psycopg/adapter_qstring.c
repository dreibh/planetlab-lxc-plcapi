/* adapter_qstring.c - QuotedString objects
 *
 * Copyright (C) 2003-2004 Federico Di Gregorio <fog@debian.org>
 *
 * This file is part of psycopg.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2,
 * or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */

#include <Python.h>
#include <structmember.h>
#include <stringobject.h>

#include <libpq-fe.h>
#include <string.h>

#define PSYCOPG_MODULE
#include "psycopg/config.h"
#include "psycopg/python.h"
#include "psycopg/psycopg.h"
#include "psycopg/connection.h"
#include "psycopg/adapter_qstring.h"
#include "psycopg/microprotocols_proto.h"


/** the quoting code */

#ifndef PSYCOPG_OWN_QUOTING
static size_t
qstring_escape(char *to, char *from, size_t len, PGconn *conn)
{
#if PG_MAJOR_VERSION > 8 || \
 (PG_MAJOR_VERSION == 8 && PG_MINOR_VERSION > 1) || \
 (PG_MAJOR_VERSION == 8 && PG_MINOR_VERSION == 1 && PG_PATCH_VERSION >= 4)
    int err;
    if (conn)
        return PQescapeStringConn(conn, to, from, len, &err);
    else
#endif
        return PQescapeString(to, from, len);
}
#else
static size_t
qstring_escape(char *to, char *from, size_t len, PGconn *conn)
{
    int i, j;

    for (i=0, j=0; i<len; i++) {
        switch(from[i]) {

        case '\'':
            to[j++] = '\'';
            to[j++] = '\'';
            break;

        case '\\':
            to[j++] = '\\';
            to[j++] = '\\';
            break;

        case '\0':
            /* do nothing, embedded \0 are discarded */
            break;

        default:
            to[j++] = from[i];
        }
    }
    to[j] = '\0';

    Dprintf("qstring_quote: to = %s", to);
    return strlen(to);
}
#endif

/* qstring_quote - do the quote process on plain and unicode strings */

static PyObject *
qstring_quote(qstringObject *self)
{
    PyObject *str;
    char *s, *buffer;
    int len;

    /* if the wrapped object is an unicode object we can encode it to match
       self->encoding but if the encoding is not specified we don't know what
       to do and we raise an exception */

    /* TODO: we need a real translation table from postgres encoding names to
           python ones here */
    
    if (PyUnicode_Check(self->wrapped) && self->encoding) {
        PyObject *enc = PyDict_GetItemString(psycoEncodings, self->encoding);
        /* note that pgenc is a borrowed reference */

        if (enc) {
            char *s = PyString_AsString(enc);
            Dprintf("qstring_quote: encoding unicode object to %s", s);
            str = PyUnicode_AsEncodedString(self->wrapped, s, NULL);
            Dprintf("qstring_quote: got encoded object at %p", str);
            if (str == NULL) return NULL;
        }
        else {
            /* can't find the right encoder, raise exception */
            PyErr_Format(InterfaceError,
                         "can't encode unicode string to %s", self->encoding);
            return NULL;
        }
    }

    /* if the wrapped object is a simple string, we don't know how to
       (re)encode it, so we pass it as-is */
    else if (PyString_Check(self->wrapped)) {
        str = self->wrapped;
        /* INCREF to make it ref-wise identical to unicode one */
        Py_INCREF(str);
    }
    
    /* if the wrapped object is not a string, this is an error */ 
    else {
        PyErr_SetString(PyExc_TypeError,
                        "can't quote non-string object (or missing encoding)");
        return NULL;
    }

    /* encode the string into buffer */
    PyString_AsStringAndSize(str, &s, &len);
        
    buffer = (char *)PyMem_Malloc((len*2+3) * sizeof(char));
    if (buffer == NULL) {
        Py_DECREF(str);
        PyErr_NoMemory();
        return NULL;
    }

    Py_BEGIN_ALLOW_THREADS;
    len = qstring_escape(buffer+1, s, len,
        self->conn ? ((connectionObject*)self->conn)->pgconn : NULL);
    buffer[0] = '\'' ; buffer[len+1] = '\'';
    Py_END_ALLOW_THREADS;
    
    self->buffer = PyString_FromStringAndSize(buffer, len+2);
    PyMem_Free(buffer);
    Py_DECREF(str);
        
    return self->buffer;
}

/* qstring_str, qstring_getquoted - return result of quoting */

static PyObject *
qstring_str(qstringObject *self)
{
    if (self->buffer == NULL) {
        qstring_quote(self);
    }
    Py_XINCREF(self->buffer);
    return self->buffer;
}

PyObject *
qstring_getquoted(qstringObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "")) return NULL;
    return qstring_str(self);
}

PyObject *
qstring_prepare(qstringObject *self, PyObject *args)
{
    connectionObject *conn;

    if (!PyArg_ParseTuple(args, "O", &conn))
        return NULL;

    /* we bother copying the encoding only if the wrapped string is unicode,
       we don't need the encoding if that's not the case */
    if (PyUnicode_Check(self->wrapped)) {
        if (self->encoding) free(self->encoding);
        self->encoding = strdup(conn->encoding);
        Dprintf("qstring_prepare: set encoding to %s", conn->encoding);
    }

    Py_XDECREF(self->conn);
    if (conn) {
        self->conn = (PyObject*)conn;
        Py_INCREF(self->conn);
    }

    Py_INCREF(Py_None);
    return Py_None;
}
    
PyObject *
qstring_conform(qstringObject *self, PyObject *args)
{
    PyObject *res, *proto;
    
    if (!PyArg_ParseTuple(args, "O", &proto)) return NULL;

    if (proto == (PyObject*)&isqlquoteType)
        res = (PyObject*)self;
    else
        res = Py_None;
    
    Py_INCREF(res);
    return res;
}

/** the QuotedString object **/

/* object member list */

static struct PyMemberDef qstringObject_members[] = {
    {"adapted", T_OBJECT, offsetof(qstringObject, wrapped), RO},
    {"buffer", T_OBJECT, offsetof(qstringObject, buffer), RO},
    {"encoding", T_STRING, offsetof(qstringObject, encoding), RO},
    {NULL}
};

/* object method table */

static PyMethodDef qstringObject_methods[] = {
    {"getquoted", (PyCFunction)qstring_getquoted, METH_VARARGS,
     "getquoted() -> wrapped object value as SQL-quoted string"},
    {"prepare", (PyCFunction)qstring_prepare, METH_VARARGS,
     "prepare(conn) -> set encoding to conn->encoding and store conn"},
    {"__conform__", (PyCFunction)qstring_conform, METH_VARARGS, NULL},
    {NULL}  /* Sentinel */
};

/* initialization and finalization methods */

static int
qstring_setup(qstringObject *self, PyObject *str, char *enc)
{
    Dprintf("qstring_setup: init qstring object at %p, refcnt = %d",
            self, ((PyObject *)self)->ob_refcnt);

    self->buffer = NULL;
    self->conn = NULL;

    /* FIXME: remove this orrible strdup */
    if (enc) self->encoding = strdup(enc);
    
    self->wrapped = str;
    Py_INCREF(self->wrapped);
    
    Dprintf("qstring_setup: good qstring object at %p, refcnt = %d",
            self, ((PyObject *)self)->ob_refcnt);
    return 0;
}

static void
qstring_dealloc(PyObject* obj)
{
    qstringObject *self = (qstringObject *)obj;

    Py_XDECREF(self->wrapped);
    Py_XDECREF(self->buffer);
    Py_XDECREF(self->conn);

    if (self->encoding) free(self->encoding);
    
    Dprintf("qstring_dealloc: deleted qstring object at %p, refcnt = %d",
            obj, obj->ob_refcnt);
    
    obj->ob_type->tp_free(obj);
}

static int
qstring_init(PyObject *obj, PyObject *args, PyObject *kwds)
{
    PyObject *str;
    char *enc = "latin-1"; /* default encoding as in Python */
    
    if (!PyArg_ParseTuple(args, "O|s", &str, &enc))
        return -1;

    return qstring_setup((qstringObject *)obj, str, enc);
}

static PyObject *
qstring_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{    
    return type->tp_alloc(type, 0);
}

static void
qstring_del(PyObject* self)
{
    PyObject_Del(self);
}

static PyObject *
qstring_repr(qstringObject *self)
{
    return PyString_FromFormat("<psycopg2._psycopg.QuotedString object at %p>", 
                                self);
}

/* object type */

#define qstringType_doc \
"QuotedString(str, enc) -> new quoted object with 'enc' encoding"

PyTypeObject qstringType = {
    PyObject_HEAD_INIT(NULL)
    0,
    "psycopg2._psycopg.QuotedString",
    sizeof(qstringObject),
    0,
    qstring_dealloc, /*tp_dealloc*/
    0,          /*tp_print*/
    0,          /*tp_getattr*/
    0,          /*tp_setattr*/   

    0,          /*tp_compare*/
    (reprfunc)qstring_repr, /*tp_repr*/
    0,          /*tp_as_number*/
    0,          /*tp_as_sequence*/
    0,          /*tp_as_mapping*/
    0,          /*tp_hash */

    0,          /*tp_call*/
    (reprfunc)qstring_str, /*tp_str*/
    0,          /*tp_getattro*/
    0,          /*tp_setattro*/
    0,          /*tp_as_buffer*/

    Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/

    qstringType_doc, /*tp_doc*/
    
    0,          /*tp_traverse*/
    0,          /*tp_clear*/

    0,          /*tp_richcompare*/
    0,          /*tp_weaklistoffset*/

    0,          /*tp_iter*/
    0,          /*tp_iternext*/

    /* Attribute descriptor and subclassing stuff */

    qstringObject_methods, /*tp_methods*/
    qstringObject_members, /*tp_members*/
    0,          /*tp_getset*/
    0,          /*tp_base*/
    0,          /*tp_dict*/
    
    0,          /*tp_descr_get*/
    0,          /*tp_descr_set*/
    0,          /*tp_dictoffset*/
    
    qstring_init, /*tp_init*/
    0, /*tp_alloc  will be set to PyType_GenericAlloc in module init*/
    qstring_new, /*tp_new*/
    (freefunc)qstring_del, /*tp_free  Low-level free-memory routine */
    0,          /*tp_is_gc For PyObject_IS_GC */
    0,          /*tp_bases*/
    0,          /*tp_mro method resolution order */
    0,          /*tp_cache*/
    0,          /*tp_subclasses*/
    0           /*tp_weaklist*/
};


/** module-level functions **/

PyObject *
psyco_QuotedString(PyObject *module, PyObject *args)
{
    PyObject *str;
    char *enc = "latin-1"; /* default encoding as in Python */
    
    if (!PyArg_ParseTuple(args, "O|s", &str, &enc))
        return NULL;
  
    return PyObject_CallFunction((PyObject *)&qstringType, "Os", str, enc);
}
