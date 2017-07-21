#
# Thierry Parmentelat - INRIA
#
# utility to clear all entries from a peer
# initially duplicated from RefreshPeer
# 

import sys

from PLC.Logger import logger
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Peers import Peer, Peers
from PLC.Sites import Site, Sites
from PLC.Persons import Person, Persons
from PLC.KeyTypes import KeyType, KeyTypes
from PLC.Keys import Key, Keys
from PLC.BootStates import BootState, BootStates
from PLC.Nodes import Node, Nodes
from PLC.SliceInstantiations import SliceInstantiations
from PLC.Slices import Slice, Slices
from PLC.Roles import Role, Roles

commit_mode = True

dry_run = False
# debug
#dry_run = True

########## helpers

def message(to_print=None, verbose_only=False):
    if verbose_only and not verbose:
        return
    logger.info(to_print)


def message_verbose(to_print=None, header='VERBOSE'):
    message("{}> {}".format(header, to_print), verbose_only=True)


class DeleteAllPeerEntries(Method):
    """
    This method is designed for situations where a federation link
    is misbehaving and one wants to restart from a clean slate.
    It is *not* designed for regular operations, but as a repairing
    tool only.

    As the name suggests, clear all local entries that are marked as
    belonging to peer peer_id - or peername
    if verbose is True said entries are only printed

    Note that remote/foreign entities cannot be deleted
    normally with the API

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(Peer.fields['peer_id'],
              Peer.fields['peername']),
    ]

    returns = Parameter(int, "1 if successful")

    def call(self, auth, peer_id_or_peername):

        peer = Peers(self.api, [peer_id_or_peername])[0]
        peer_id = peer['peer_id']
        peername = peer['peername']

        logger.info("DeleteAllPeerEntries on peer {} = {}"
                    .format(peername, peer_id))
        for singular, plural in (
                (Slice, Slices),
                (Key, Keys),
                (Person, Persons),
                (Node, Nodes),
                (Site, Sites)):
            classname = singular.__name__
            objs = plural(self.api, {'peer_id': peer_id})
            print("Found {len} {classname}s from peer {peername}"
                  .format(len=len(objs),
                          classname=classname,
                          peername=peername))
            if dry_run:
                print("dry-run mode: skipping actual deletion")
            else:
                print("Deleting {classname}s".format(classname=classname))
                for obj in objs:
                    print '.',
                    sys.stdout.flush()
                    obj.delete(commit=commit_mode)
                print

        # Update peer itself and commit
        peer.sync(commit=True)

        return 1
