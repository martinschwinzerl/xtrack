import json
from cpymad.madx import Madx
import pysixtrack

p0c = 25.92e9

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif np.issubdtype(type(obj), np.integer):
            return int(obj)
        return json.JSONEncoder.default(self, obj)


mad = Madx()
mad.call('sps_thin.seq')

line_without_spacecharge = pysixtrack.Line.from_madx_sequence(
                                            mad.sequence['sps'],
                                            install_apertures=True)
# enable RF
i_cavity = line_without_spacecharge.element_names.index('acta.31637')
line_without_spacecharge.elements[i_cavity].voltage = 3e6
line_without_spacecharge.elements[i_cavity].lag = 180.

part = pysixtrack.Particles(p0c=p0c, x=2e-3, y=3e-3, zeta=20e-2)

with open('line_no_spacecharge_and_particle.json', 'w') as fid:
    json.dump({
        'line': line_without_spacecharge.to_dict(keepextra=True),
        'particle': part.to_dict()},
        fid, cls=Encoder)

import pysixtrack.be_beamfields.tools as bt
sc_locations, sc_lengths = bt.determine_sc_locations(
    line=line_without_spacecharge,
    n_SCkicks = 540,
    length_fuzzy=0)

# Install spacecharge place holders
sc_names = ['sc%d' % number for number in range(len(sc_locations))]
bt.install_sc_placeholders(
    mad, 'sps', sc_names, sc_locations, mode='Bunched')

# Generate line with spacecharge
line_with_spacecharge = pysixtrack.Line.from_madx_sequence(
                                       mad.sequence['sps'],
                                       install_apertures=True)

# Get spacecharge names and twiss info from optics
mad_sc_names, sc_twdata = bt.get_spacecharge_names_twdata(
    mad, 'sps', mode='Bunched')

# Setup spacecharge
sc_elements, sc_names = line_with_spacecharge.get_elements_of_type(
        pysixtrack.elements.SCQGaussProfile
    )
bt.setup_spacecharge_bunched_in_line(
        sc_elements=sc_elements,
        sc_lengths=sc_lengths,
        sc_twdata=sc_twdata,
        betagamma=part.beta0*part.gamma0,
        number_of_particles=1e11,
        delta_rms=1e-4,
        neps_x=1.5e-6,
        neps_y=2e-6,
        bunchlength_rms=10e-2
    )

# enable RF
i_cavity = line_with_spacecharge.element_names.index('acta.31637')
line_with_spacecharge.elements[i_cavity].voltage = 3e6
line_with_spacecharge.elements[i_cavity].lag = 180.

with open('line_with_spacecharge_and_particle.json', 'w') as fid:
    json.dump({
        'line': line_with_spacecharge.to_dict(keepextra=True),
        'particle': part.to_dict()},
        fid, cls=Encoder)
