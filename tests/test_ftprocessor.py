"""Unit tests for Fourier transforms

realtimcornwell@gmail.com
"""
import unittest

import numpy
from numpy.testing import assert_allclose

from astropy.coordinates import SkyCoord
from astropy import units as u

from arl.skymodel_operations import create_skycomponent
from arl.testing_support import create_named_configuration, filter_configuration
from arl.skymodel_operations import create_skymodel_from_component
from arl.visibility_operations import create_visibility
#from arl.fourier_transforms import predict_visibility
from arl.ftprocessor import *

import logging
log = logging.getLogger( "tests.test_ftprocessor" )


class TestFTProcessor(unittest.TestCase):

    def setUp(self):
        
        self.params = {'wstep': 10.0, 'npixel': 512, 'cellsize':0.0002, 'spectral_mode': 'channel'}
        
        self.field_of_view = self.params['npixel'] * self.params['cellsize']
        self.uvmax = 0.3 / self.params['cellsize']
        
        vlaa = filter_configuration(create_named_configuration('VLAA'), self.params)
        vlaa.data['xyz'] *= 1.0 / 30.0
        times = numpy.arange(-3.0, +3.0, 6.0 / 60.0) * numpy.pi / 12.0
        frequency = numpy.arange(1.0e8, 1.50e8, 2.0e7)
        
        # Define the component and give it some spectral behaviour
        f=numpy.array([100.0, 20.0, -10.0, 1.0])
        self.flux = numpy.array([f,0.8*f,0.6*f])
        self.average = numpy.average(self.flux[:,0])
        # The phase centre is absolute and the component is specified relative (for now).
        # This means that the component should end up at the position phasecentre+compredirection
        self.phasecentre      = SkyCoord(ra=+15.0*u.deg, dec=+35.0*u.deg, frame='icrs', equinox=2000.0)
        self.compabsdirection = SkyCoord(ra=17.0*u.deg,  dec=+36.5*u.deg, frame='icrs', equinox=2000.0)
        # TODO: convert entire mechanism to absolute coordinates
        pcof=self.phasecentre.skyoffset_frame()
        self.compreldirection = self.compabsdirection.transform_to(pcof)
        self.comp = create_skycomponent(flux=self.flux, frequency=frequency, direction=self.compreldirection)
        self.sm = create_skymodel_from_component(self.comp)
        self.vis = create_visibility(vlaa, times, frequency, weight=1.0, phasecentre=self.phasecentre,
                                   params=self.params)
#        self.vismodel = predict_visibility(self.vis, self.sm, self.params)


    # def test_2d(self):
    #     ftp = ftprocessor_2d(self.field_of_view, self.uvmax, self.model, self.vis, kernel=None, params=self.params)
    #     pass
    #
    def test_all(self):
        vis = object()
        model = object()
        for ftpfunc in [ftprocessor_base, ftprocessor_2d, ftprocessor_wprojection, ftprocessor_image_partition]:
            ftp = ftpfunc(field_of_view=self.field_of_view, uvmax=self.uvmax, model=model, vis=self.vis,
                          kernel=None, params=self.params)
            while ftp.next():
                ftp.invert()
                ftp.predict()

    def test_image_partitioning(self):
        pass


    def test_uv_partitioning(self):
        pass


    def test_wprojection(self):
        pass


if __name__ == '__main__':
    import sys
    import logging
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler(sys.stdout))
    unittest.main()