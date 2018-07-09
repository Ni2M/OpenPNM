import scipy as _sp
from scipy import pi


def hagen_poiseuille(target,
                     pore_viscosity='pore.viscosity',
                     throat_viscosity='throat.viscosity',
                     throat_equivalent_area='throat.equivalent_area',
                     throat_conduit_lengths='throat.conduit_lengths'):
    r"""
    Calculate the hydraulic conductance of conduits in network, where a
    conduit is ( 1/2 pore - full throat - 1/2 pore ) based on the areas

    Parameters
    ----------
    target : OpenPNM Object
        The object which this model is associated with. This controls the
        length of the calculated array, and also provides access to other
        necessary properties.

    pore_viscosity : string
        Dictionary key of the pore viscosity values

    throat_viscosity : string
        Dictionary key of the throat viscosity values

    throat_equivalent_area : string
        Dictionary key of the throat equivalent area values

    throat_conduit_lengths : string
        Dictionary key of the throat conduit lengths

    Notes
    -----
    (1) This function requires that all the necessary phase properties already
    be calculated.

    (2) This function calculates the specified property for the *entire*
    network then extracts the values for the appropriate throats at the end.

    (3) This function assumes cylindrical/rectangular throats (for 3d/2d)

    """
    network = target.project.network
    is2d = True if 1 in network._shape else False
    is2d = False
    throats = network.map_throats(target['throat._id'])
    phase = target.project.find_phase(target)
    geom = target.project.find_geometry(target)
    cn = network['throat.conns'][throats]
    # Getting equivalent areas
    A1 = geom[throat_equivalent_area+'.pore1'][throats]
    At = geom[throat_equivalent_area+'.throat'][throats]
    A2 = geom[throat_equivalent_area+'.pore2'][throats]
    # Getting conduit lengths
    L1 = geom[throat_conduit_lengths+'.pore1'][throats]
    Lt = geom[throat_conduit_lengths+'.throat'][throats]
    L2 = geom[throat_conduit_lengths+'.pore2'][throats]
    # Interpolate pore phase property values to throats
    try:
        mut = phase[throat_viscosity]
    except KeyError:
        mut = phase.interpolate_data(propname=pore_viscosity)
    try:
        mup = phase[pore_viscosity]
    except KeyError:
        mup = phase.interpolate_data(propname=throat_viscosity)
    # Find g for half of pore 1
    gp1 = A1**3/(12*pi*mup[cn[:, 0]]*L1) if is2d else A1**2/(8*pi*mup[cn[:, 0]]*L1)
    gp1[_sp.isnan(gp1)] = _sp.inf
    # Find g for half of pore 2
    gp2 = A2**3/(12*pi*mup[cn[:, 1]]*L2) if is2d else A2**2/(8*pi*mup[cn[:, 1]]*L2)
    gp2[_sp.isnan(gp2)] = _sp.inf
    # Find g for full throat
    gt = At**3/(12*pi*mup[throats]*Lt) if is2d else At**2/(8*pi*mut[throats]*Lt)
    gt[_sp.isnan(gt)] = _sp.inf
    return (1/gt + 1/gp1 + 1/gp2)**(-1)
