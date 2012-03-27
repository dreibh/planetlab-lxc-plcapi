# Marc E. Fiuczynski <mef@cs.princeton.edu>
# Copyright (C) 2004 The Trustees of Princeton University
#
# Client ping of death program for both udp & icmp
#
# modified for inclusion by api by Aaron K

import struct
import os
import array
import getopt
from socket import *

UPOD_PORT = 664

def _in_cksum(packet):
    """THE RFC792 states: 'The 16 bit one's complement of
    the one's complement sum of all 16 bit words in the header.'
    Generates a checksum of a (ICMP) packet. Based on in_chksum found
    in ping.c on FreeBSD.
    """

    # add byte if not dividable by 2
    if len(packet) & 1:
        packet = packet + '\0'

    # split into 16-bit word and insert into a binary array
    words = array.array('h', packet)
    sum = 0

    # perform ones complement arithmetic on 16-bit words
    for word in words:
        sum += (word & 0xffff)

    hi = sum >> 16
    lo = sum & 0xffff
    sum = hi + lo
    sum = sum + (sum >> 16)

    return (~sum) & 0xffff # return ones complement

def _construct(id, data):
    """Constructs a ICMP IPOD packet
    """
    ICMP_TYPE = 6 # ping of death code used by PLK
    ICMP_CODE = 0
    ICMP_CHECKSUM = 0
    ICMP_ID = 0
    ICMP_SEQ_NR = 0

    header = struct.pack('bbHHh', ICMP_TYPE, ICMP_CODE, ICMP_CHECKSUM, \
                         ICMP_ID, ICMP_SEQ_NR+id)

    packet = header + data          # ping packet without checksum
    checksum = _in_cksum(packet)    # make checksum

    # construct header with correct checksum
    header = struct.pack('bbHHh', ICMP_TYPE, ICMP_CODE, checksum, ICMP_ID, \
                         ICMP_SEQ_NR+id)

    # ping packet *with* checksum
    packet = header + data

    # a perfectly formatted ICMP echo packet
    return packet

def icmp_pod(host,key):
    uid = os.getuid()
    if uid <> 0:
        print "must be root to send icmp pod"
        return

    s = socket(AF_INET, SOCK_RAW, getprotobyname("icmp"))
    packet = _construct(0, key) # make a ping packet
    addr = (host,1)
    print 'pod sending icmp-based reboot request to %s' % host
    for i in range(1,10):
        s.sendto(packet, addr)

def udp_pod(host,key,fromaddr=('', 0)):
    addr = host, UPOD_PORT
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(fromaddr)
    packet = key
    print 'pod sending udp-based reboot request to %s' % host
    for i in range(1,10):
        s.sendto(packet, addr)

def noop_pod(host,key):
    pass
