# Copyright 2012 mdtraj developers
#
# This file is part of mdtraj
#
# mdtraj is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# mdtraj is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# mdtraj. If not, see http://www.gnu.org/licenses/.

"""
Tests for the AMBER netcdf reader/writer code
"""

from mdtraj import netcdf
import os, tempfile
from nose.tools import assert_raises
import numpy as np
from mdtraj.testing import get_fn, eq, DocStringFormatTester

TestDocstrings = DocStringFormatTester(netcdf, error_on_none=True)

temp = tempfile.mkstemp(suffix='.nc')[1]
def teardown_module(module):
    """remove the temporary file created by tests in this file
    this gets automatically called by nose"""
    os.unlink(temp)


def test_read_after_close():
    f = netcdf.NetCDFTrajectoryFile(get_fn('mdcrd.nc'))
    yield lambda: eq(f.n_atoms, 223)
    yield lambda: eq(f.n_frames, 101)

    f.close()

    with assert_raises(IOError):
        # should be an ioerror if you read a file that's closed
        eq(f.read(), 1)


def test_write_without_clobber():
    # opening a file for writing without explicitly setting force_overwrite
    # is not cool
    with assert_raises(RuntimeError):
        f = netcdf.NetCDFTrajectoryFile(get_fn('mdcrd.nc'), 'w')


def test_shape():
    xyz, time, boxlength, boxangles = netcdf.NetCDFTrajectoryFile(get_fn('mdcrd.nc')).read()

    yield lambda: eq(xyz.shape, (101, 223, 3))
    yield lambda: eq(time.shape, (101,))
    yield lambda: eq(boxlength, None)
    yield lambda: eq(boxangles, None)


def test_read_chunk_1():
    with netcdf.NetCDFTrajectoryFile(get_fn('mdcrd.nc')) as f:
        a, b, c, d = f.read(10)
        e, f, g, h = f.read()

        yield lambda: eq(len(a), 10)
        yield lambda: eq(len(b), 10)

        yield lambda: eq(len(e), 101-10)
        yield lambda: eq(len(f), 101-10)

    xyz = netcdf.NetCDFTrajectoryFile(get_fn('mdcrd.nc')).read()[0]

    yield lambda: eq(a, xyz[0:10])
    yield lambda: eq(e, xyz[10:])


def test_read_chunk_2():
    with netcdf.NetCDFTrajectoryFile(get_fn('mdcrd.nc')) as f:
        a, b, c, d = f.read(10)
        e, f, g, h = f.read(100000000000)

        yield lambda: eq(len(a), 10)
        yield lambda: eq(len(b), 10)

        yield lambda: eq(len(e), 101-10)
        yield lambda: eq(len(f), 101-10)

    xyz = netcdf.NetCDFTrajectoryFile(get_fn('mdcrd.nc')).read()[0]

    yield lambda: eq(a, xyz[0:10])
    yield lambda: eq(e, xyz[10:])


def test_read_chunk_3():
    # too big of a chunk should not be an issue
    a = netcdf.NetCDFTrajectoryFile(get_fn('mdcrd.nc')).read(1000000000)
    b = netcdf.NetCDFTrajectoryFile(get_fn('mdcrd.nc')).read()

    eq(a[0], b[0])


def test_read_write_1():
    xyz = np.random.randn(100, 3, 3)
    time = np.random.randn(100)
    boxlengths = np.random.randn(100, 3)
    boxangles = np.random.randn(100, 3)

    with netcdf.NetCDFTrajectoryFile(temp, 'w', force_overwrite=True) as f:
        f.write(xyz, time, boxlengths, boxangles)

    with netcdf.NetCDFTrajectoryFile(temp) as f:
        a, b, c, d = f.read()
        yield lambda: eq(a, xyz)
        yield lambda: eq(b, time)
        yield lambda: eq(c, boxlengths)
        yield lambda: eq(d, boxangles)


def test_read_write_2():
    xyz = np.random.randn(100, 3, 3)
    time = np.random.randn(100)

    with netcdf.NetCDFTrajectoryFile(temp, 'w', force_overwrite=True) as f:
        f.write(xyz, time)

    with netcdf.NetCDFTrajectoryFile(temp) as f:
        a, b, c, d = f.read()
        yield lambda: eq(a, xyz)
        yield lambda: eq(b, time)
        yield lambda: eq(c.mask, np.ma.masked_all((100,3)).mask)
        yield lambda: eq(d.mask, np.ma.masked_all((100,3)).mask)


def test_read_write_25():
    xyz = np.random.randn(100, 3, 3)
    time = np.random.randn(100)

    with netcdf.NetCDFTrajectoryFile(temp, 'w', force_overwrite=True) as f:
        f.write(xyz, time)
        f.write(xyz, time)

    with netcdf.NetCDFTrajectoryFile(temp) as f:
        a, b, c, d = f.read()
        yield lambda: eq(a[0:100], xyz)
        yield lambda: eq(b[0:100], time)
        yield lambda: eq(c.mask[0:100], np.ma.masked_all((100,3)).mask)
        yield lambda: eq(d.mask[0:100], np.ma.masked_all((100,3)).mask)

        yield lambda: eq(a[100:], xyz)
        yield lambda: eq(b[100:], time)
        yield lambda: eq(c.mask[100:], np.ma.masked_all((100,3)).mask)
        yield lambda: eq(d.mask[100:], np.ma.masked_all((100,3)).mask)

def test_write_3():
    xyz = np.random.randn(100, 3, 3)
    time = np.random.randn(100)

    with netcdf.NetCDFTrajectoryFile(temp, 'w', force_overwrite=True) as f:
        with assert_raises(ValueError):
            # you can't supply cell_lengths without cell_angles
            f.write(np.random.randn(100, 3, 3), cell_lengths=np.random.randn(100, 3))
        with assert_raises(ValueError):
            # or the other way aroun
            f.write(np.random.randn(100, 3, 3), cell_angles=np.random.randn(100, 3))


def test_n_atoms():
    with netcdf.NetCDFTrajectoryFile(temp, 'w', force_overwrite=True) as f:
        f.write(np.random.randn(1,11,3))
    with netcdf.NetCDFTrajectoryFile(temp) as f:
        eq(f.n_atoms, 11)
