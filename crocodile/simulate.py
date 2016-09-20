# Bojan Nikolic <b.nikolic@mrao.cam.ac.uk>

"""Simulate data observed by an interferometer

USEFUL NOTES
---------------------------------------------------------------------------------

From http://casa.nrao.edu/Memos/CoordConvention.pdf :

UVW is a right-handed coordinate system, with W pointing towards the
source, and a baseline convention of :math:`ant2 - ant1` where
:math:`index(ant1) < index(ant2)`.  Consider an XYZ Celestial
coordinate system centered at the location of the interferometer, with
:math:`X` towards the East, :math:`Z` towards the NCP and :math:`Y` to
complete a right-handed system. The UVW coordinate system is then
defined by the hour-angle and declination of the phase-reference
direction such that

1. when the direction of observation is the NCP (`ha=0,dec=90`),
   the UVW coordinates are aligned with XYZ,

2. V, W and the NCP are always on a Great circle,

3. when W is on the local meridian, U points East

4. when the direction of observation is at zero declination, an
   hour-angle of -6 hours makes W point due East.

The :math:`(l,m,n)` coordinates are parallel to :math:`(u,v,w)` such
that :math:`l` increases with Right-Ascension (or increasing longitude
coordinate), :math:`m` increases with Declination, and :math:`n` is
towards the source. With this convention, images will have Right
Ascension increasing from Right to Left, and Declination increasing
from Bottom to Top.

Changes
---------------------------------------------------------------------------------

[150323 - AMS]    Correction to rot(), introduced -1 factor in v calculation.
                  Change to bsl(), to agree with casa convention.

"""

import numpy
from astropy.coordinates import SkyCoord, CartesianRepresentation

# ---------------------------------------------------------------------------------

def xyz_at_latitude(local_xyz, lat):
    """
    Rotate local XYZ coordinates into celestial XYZ coordinates. These
    coordinate systems are very similar, with X pointing towards the
    geographical east in both cases. However, before the rotation Z
    points towards the zenith, whereas afterwards it will point towards
    celestial north (parallel to the earth axis).

    :param lat:
    :param local_xyz: Array of local XYZ coordinates
    :returns: Celestial XYZ coordinates
    """

    x, y, z = numpy.hsplit(local_xyz, 3)

    lat2 = numpy.pi / 2 - lat
    y2 = -z * numpy.sin(lat2) + y * numpy.cos(lat2)
    z2 = z * numpy.cos(lat2) + y * numpy.sin(lat2)

    return numpy.hstack([x, y2, z2])


# ---------------------------------------------------------------------------------

def xyz_to_uvw(ants_xyz, ha, dec):
    """
    Rotate :math:`(x,y,z)` antenna positions in earth coordinates
    to :math:`(u,v,w)` coordinates relative to
    astronomical source position :math:`(ra, dec)`.

    (see note on co-ordinate systems in header)

    :param ants_xyz: :math:`(x,y,z)` co-ordinates of antennas in array
    :param ha: hour angle of phase tracking centre (:math:`ha = ra - lst`)
    :param dec: declination of phase tracking centre
    """

    x, y, z = numpy.hsplit(ants_xyz, 3)

    u = x * numpy.cos(ha) - y * numpy.sin(ha)
    v0 = x * numpy.sin(ha) + y * numpy.cos(ha)
    v = z * numpy.cos(dec) + v0 * numpy.sin(dec)
    w = z * numpy.sin(dec) - v0 * numpy.cos(dec)

    ants_uvw = numpy.hstack([u, v, w])

    return ants_uvw


# ---------------------------------------------------------------------------------

def baselines(ants_uvw):
    """
    Compute baselines in uvw co-ordinate system from
    uvw co-ordinate system station positions

    :param ants_uvw: `(u,v,w)` co-ordinates of antennas in array
    """

    res = []
    for i in range(ants_uvw.shape[0]):
        for j in range(i + 1, ants_uvw.shape[0]):
            res.append(ants_uvw[j] - ants_uvw[i])

    basel_uvw = numpy.array(res)

    return basel_uvw


# ---------------------------------------------------------------------------------

def xyz_to_baselines(ants_xyz, ha_range, dec):
    """
    Calculate baselines in :math:`(u,v,w)` co-ordinate system
    for a range of hour angles (i.e. non-snapshot observation)
    to create a uvw sampling distribution

    :param ants_xyz: :math:`(x,y,z)` co-ordinates of antennas in array
    :param ha_range: list of hour angle values for astronomical source as function of time
    :param dec: declination of astronomical source [constant, not :math:`f(t)`]
    """

    dist_uvw = numpy.concatenate([baselines(xyz_to_uvw(ants_xyz, hax, dec)) for hax in ha_range])
    return dist_uvw

# ---------------------------------------------------------------------------------

def skycoord_to_lmn(pos: SkyCoord, phasecentre: SkyCoord):
    """
    Convert astropy sky coordinates into the l,m,n coordinate system
    relative to a phase centre.

    The l,m,n is a RHS coordinate system with
    * its origin on the sky sphere
    * m,n and the celestial north on the same plane
    * l,m a tangential plane of the sky sphere

    Note that this means that l increases east-wards
    """

    # Determine relative sky position
    todc = pos.transform_to(phasecentre.skyoffset_frame())
    dc = todc.represent_as(CartesianRepresentation)

    # Do coordinate transformation - astropy's relative coordinates do
    # not quite follow imaging conventions
    return dc.y, dc.z, dc.x-1

# ---------------------------------------------------------------------------------

def simulate_point(dist_uvw, l, m):
    """
    Simulate visibilities for unit amplitude point source at
    direction cosines (l,m) relative to the phase centre.
    
    This includes phase tracking to the centre of the field (hence the minus 1
    in the exponent.)

    Note that point source is delta function, therefore the
    FT relationship becomes an exponential, evaluated at
    (uvw.lmn)

    :param dist_uvw: :math:`(u,v,w)` distribution of projected baselines
    :param l: horizontal direction cosine relative to phase tracking centre
    :param m: orthogonal directon cosine relative to phase tracking centre
    """

    # vector direction to source
    s = numpy.array([l, m, numpy.sqrt(1 - l ** 2 - m ** 2) - 1.0])
    # complex valued Visibility data
    return numpy.exp(-2j * numpy.pi * numpy.dot(dist_uvw, s))


if __name__ == '__main__':
    import tests.test_test_support

    unittest.main()
