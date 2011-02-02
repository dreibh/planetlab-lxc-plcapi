from PLC.Method import Method
from PLC.Auth import Auth
from PLC.Faults import *
from PLC.Parameter import *
from PLC.Slices import Slice, Slices

from PLC.Accessors.Accessors_standard import *                  # import slice accessors
from PLC.Accessors.Accessors_sliverauth import *                # import slice accessors

class GetSliceFamily(Method):
    """
    Returns the slice vserver reference image that a given slice
    should be based on. This depends on the global PLC settings in the
    PLC_FLAVOUR area, optionnally overridden by any of the 'vref',
    'arch', 'pldistro', 'fcdistro' tag if set on the slice.
    """

    roles = ['admin', 'user', 'node']

    # don't support sliver-specific settings yet
    accepts = [
        Auth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
        ]

    returns = Parameter (str, "the slicefamily this slice should be based upon")

    #
    ### system slices - at least planetflow - still rely on 'vref'
    #
    def call(self, auth, slice_id_or_name):
        # Get slice information
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice %r"%slice_id_or_name
        slice = slices[0]
        slice_id = slice['slice_id']

        arch = GetSliceArch (self.api,self.caller).call(auth,slice_id)
        if not arch: arch = self.api.config.PLC_FLAVOUR_SLICE_ARCH

        pldistro = GetSlicePldistro (self.api,self.caller).call(auth, slice_id)
        if not pldistro: pldistro = self.api.config.PLC_FLAVOUR_SLICE_PLDISTRO

        fcdistro = GetSliceFcdistro (self.api,self.caller).call(auth, slice_id)
        if not fcdistro: fcdistro = self.api.config.PLC_FLAVOUR_SLICE_FCDISTRO

        # the vref tag, if set, wins over pldistro
        vref = GetSliceVref (self.api,self.caller).call(auth,slice_id)

        # omf-control'ed slivers need the omf vserver reference image
        # we used to issue SetSliceVref (self.api) (auth,slice_id,'omf')
        # to avoid asking users to set both tags 'omf_control' and 'vref'
        # however we can't use SetSliceVref here because a node is only allowed 
        # to set a sliver tag, not a slice tag
        # and this somehow gets called from GetSlivers
        # anyways it was a bad idea, let's have the UI do that instead

        # xxx would make sense to check the corresponding vserver rpms are available
        # in all node-families yum repos (and yumgroups, btw)
        if vref:
            return "%s-%s-%s"%(vref,fcdistro,arch)
        else:
            return "%s-%s-%s"%(pldistro,fcdistro,arch)
