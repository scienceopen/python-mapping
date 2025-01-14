""" transforms involving ECI earth-centered inertial """

from __future__ import annotations

from datetime import datetime

import numpy

try:
    import astropy.units as u
    from astropy.coordinates import GCRS, ITRS, CartesianRepresentation, EarthLocation
except ImportError:
    pass

from .sidereal import greenwichsrt, juliandate

__all__ = ["eci2ecef", "ecef2eci"]


def eci2ecef(x, y, z, time: datetime) -> tuple:
    """
    Observer => Point  ECI  =>  ECEF

    J2000 frame

    Parameters
    ----------
    x : float
        ECI x-location [meters]
    y : float
        ECI y-location [meters]
    z : float
        ECI z-location [meters]
    time : datetime.datetime
        time of obsevation (UTC)

    Results
    -------
    x_ecef : float
        x ECEF coordinate
    y_ecef : float
        y ECEF coordinate
    z_ecef : float
        z ECEF coordinate
    """

    try:
        return eci2ecef_astropy(x, y, z, time)
    except NameError:
        return eci2ecef_numpy(x, y, z, time)


def eci2ecef_astropy(x, y, z, t: datetime) -> tuple:
    """
    eci2ecef using Astropy

    see eci2ecef() for description
    """

    gcrs = GCRS(CartesianRepresentation(x * u.m, y * u.m, z * u.m), obstime=t)
    itrs = gcrs.transform_to(ITRS(obstime=t))

    x_ecef = itrs.x.value
    y_ecef = itrs.y.value
    z_ecef = itrs.z.value

    return x_ecef, y_ecef, z_ecef


def eci2ecef_numpy(x, y, z, t: datetime) -> tuple:
    """
    eci2ecef using Numpy

    see eci2ecef() for description
    """

    x = numpy.atleast_1d(x)
    y = numpy.atleast_1d(y)
    z = numpy.atleast_1d(z)
    gst = numpy.atleast_1d(greenwichsrt(juliandate(t)))
    assert (
        x.shape == y.shape == z.shape
    ), f"shape mismatch: x: ${x.shape}  y: {y.shape}  z: {z.shape}"

    if gst.size == 1 and x.size != 1:
        gst = numpy.broadcast_to(gst, x.shape[0])
    assert x.size == gst.size, f"shape mismatch: x: {x.shape}  gst: {gst.shape}"

    eci = numpy.column_stack((x.ravel(), y.ravel(), z.ravel()))
    ecef = numpy.empty((x.size, 3))
    for i in range(eci.shape[0]):
        ecef[i, :] = R3(gst[i]) @ eci[i, :].T

    x_ecef = ecef[:, 0].reshape(x.shape)
    y_ecef = ecef[:, 1].reshape(y.shape)
    z_ecef = ecef[:, 2].reshape(z.shape)

    return x_ecef.squeeze()[()], y_ecef.squeeze()[()], z_ecef.squeeze()[()]


def ecef2eci(x, y, z, time: datetime) -> tuple:
    """
    Point => Point   ECEF => ECI

    J2000 frame

    Parameters
    ----------

    x : float
        target x ECEF coordinate
    y : float
        target y ECEF coordinate
    z : float
        target z ECEF coordinate
    time : datetime.datetime
        time of observation

    Results
    -------
    x_eci : float
        x ECI coordinate
    y_eci : float
        y ECI coordinate
    z_eci : float
        z ECI coordinate
    """

    try:
        return ecef2eci_astropy(x, y, z, time)
    except NameError:
        return ecef2eci_numpy(x, y, z, time)


def ecef2eci_astropy(x, y, z, t: datetime) -> tuple:
    """ecef2eci using Astropy
    see ecef2eci() for description
    """
    itrs = ITRS(CartesianRepresentation(x * u.m, y * u.m, z * u.m), obstime=t)
    gcrs = itrs.transform_to(GCRS(obstime=t))
    eci = EarthLocation(*gcrs.cartesian.xyz)

    x_eci = eci.x.value
    y_eci = eci.y.value
    z_eci = eci.z.value

    return x_eci, y_eci, z_eci


def ecef2eci_numpy(x, y, z, t: datetime) -> tuple:
    """ecef2eci using Numpy
    see ecef2eci() for description
    """

    x = numpy.atleast_1d(x)
    y = numpy.atleast_1d(y)
    z = numpy.atleast_1d(z)
    gst = numpy.atleast_1d(greenwichsrt(juliandate(t)))
    assert x.shape == y.shape == z.shape
    assert x.size == gst.size

    ecef = numpy.column_stack((x.ravel(), y.ravel(), z.ravel()))
    eci = numpy.empty((x.size, 3))
    for i in range(x.size):
        eci[i, :] = R3(gst[i]).T @ ecef[i, :]

    x_eci = eci[:, 0].reshape(x.shape)
    y_eci = eci[:, 1].reshape(y.shape)
    z_eci = eci[:, 2].reshape(z.shape)

    return x_eci.squeeze()[()], y_eci.squeeze()[()], z_eci.squeeze()[()]


def R3(x: float):
    """Rotation matrix for ECI"""
    return numpy.array(
        [[numpy.cos(x), numpy.sin(x), 0], [-numpy.sin(x), numpy.cos(x), 0], [0, 0, 1]]
    )
