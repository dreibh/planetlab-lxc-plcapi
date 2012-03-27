from PLC.Methods.SliceGetTicket import SliceGetTicket

class SliceTicketGet(SliceGetTicket):
    """
    Deprecated. See GetSliceTicket.

    Warning: This function exists solely for backward compatibility
    with the old public PlanetLab 3.0 Node Manager, which will be
    removed from service by 2007. This call is not intended to be used
    by any other PLC except the public PlanetLab.
    """

    status = "deprecated"
