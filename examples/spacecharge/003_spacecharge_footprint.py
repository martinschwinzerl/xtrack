import pathlib
import json
import numpy as np

import xobjects as xo
import xline as xl
import xpart as xp
import xtrack as xt
import xfields as xf

fname_sequence = ('../../test_data/sps_w_spacecharge/'
                  'line_with_spacecharge_and_particle.json')

fname_optics = ('../../test_data/sps_w_spacecharge/'
                'optics_and_co_at_start_ring.json')

seq_name = 'sps'
bunch_intensity = 1e11/3
sigma_z = 22.5e-2/3
neps_x=2.5e-6
neps_y=2.5e-6
n_part=int(1e6)
rf_voltage=3e6
num_turns=32

mode = 'frozen'
mode = 'quasi-frozen'
mode = 'pic'

####################
# Choose a context #
####################

#context = xo.ContextCpu()
context = xo.ContextCupy()
#context = xo.ContextPyopencl('0.0')

_buffer = context.new_buffer()

print(context)

##################
# Get a sequence #
##################

with open(fname_sequence, 'r') as fid:
     input_data = json.load(fid)
sequence = xl.Line.from_dict(input_data['line'])

first_sc = sequence.elements[1]
sigma_x = first_sc.sigma_x
sigma_y = first_sc.sigma_y

##########################
# Configure space-charge #
##########################

if mode == 'frozen':
    pass # Already configured in line
elif mode == 'quasi-frozen':
    xf.replace_spaceharge_with_quasi_frozen(
                                    sequence, _buffer=_buffer,
                                    update_mean_x_on_track=True,
                                    update_mean_y_on_track=True)
elif mode == 'pic':
    pic_collection, all_pics = xf.replace_spaceharge_with_PIC(
        _context=context, sequence=sequence,
        n_sigmas_range_pic_x=8,
        n_sigmas_range_pic_y=8,
        nx_grid=256, ny_grid=256, nz_grid=100,
        n_lims_x=7, n_lims_y=3,
        z_range=(-3*sigma_z, 3*sigma_z))
else:
    raise ValueError(f'Invalid mode: {mode}')

########################
# Get optics and orbit #
########################

with open(fname_optics, 'r') as fid:
    ddd = json.load(fid)
part_on_co = xp.Particles.from_dict(ddd['particle_on_madx_co'])
RR = np.array(ddd['RR_madx'])


#################
# Build Tracker #
#################
tracker = xt.Tracker(_buffer=_buffer,
                    sequence=sequence)

####################################
# Generate particles for footprint #
####################################

part = xp.generate_matched_gaussian_bunch(
         num_particles=n_part, total_intensity_particles=bunch_intensity,
         nemitt_x=neps_x, nemitt_y=neps_y, sigma_z=sigma_z,
         particle_on_co=part_on_co, R_matrix=RR,
         circumference=6911., alpha_momentum_compaction=0.0030777,
         rf_harmonic=4620, rf_voltage=rf_voltage, rf_phase=0)

import footprint
r_max_sigma = 5
N_r_footprint = 10
N_theta_footprint = 8
xy_norm = footprint.initial_xy_polar(
        r_min=0.3, r_max=r_max_sigma,
        r_N=N_r_footprint + 1,
        theta_min=0.05 * np.pi / 2,
        theta_max=np.pi / 2 - 0.05 * np.pi / 2,
        theta_N=N_theta_footprint)

N_footprint = len(xy_norm[:, :, 0].flatten())
part.x[:N_footprint] = sigma_x*xy_norm[:, :, 0].flatten()
part.y[:N_footprint] = sigma_y*xy_norm[:, :, 1].flatten()
part.px[:N_footprint] = 0.
part.py[:N_footprint] = 0.
part.zeta[:N_footprint] = 0.
part._delta[:N_footprint] = 0.
part._rpp[:N_footprint] = 0.
part._rvv[:N_footprint] = 0.

xtparticles = xt.Particles(_context=context, **part.to_dict())

#########
# Track #
#########
x_tbt = np.zeros((N_footprint, num_turns), dtype=np.float64)
y_tbt = np.zeros((N_footprint, num_turns), dtype=np.float64)
for ii in range(num_turns):
    print(f'Turn: {ii}', end='\r', flush=True)
    x_tbt[:, ii] = context.nparray_from_context_array(xtparticles.x[:N_footprint]).copy()
    y_tbt[:, ii] = context.nparray_from_context_array(xtparticles.y[:N_footprint]).copy()
    tracker.track(xtparticles)

######################
# Frequency analysis #
######################
import NAFFlib

Qx = np.zeros(N_footprint)
Qy = np.zeros(N_footprint)

for i_part in range(N_footprint):
    Qx[i_part] = NAFFlib.get_tune(x_tbt[i_part, :])
    Qy[i_part] = NAFFlib.get_tune(y_tbt[i_part, :])

Qxy_fp = np.zeros_like(xy_norm)

Qxy_fp[:, :, 0] = np.reshape(Qx, Qxy_fp[:, :, 0].shape)
Qxy_fp[:, :, 1] = np.reshape(Qy, Qxy_fp[:, :, 1].shape)

import matplotlib.pyplot as plt
plt.close('all')

fig3 = plt.figure(3)
axcoord = fig3.add_subplot(1, 1, 1)
footprint.draw_footprint(xy_norm, axis_object=axcoord, linewidth = 1)
axcoord.set_xlim(right=np.max(xy_norm[:, :, 0]))
axcoord.set_ylim(top=np.max(xy_norm[:, :, 1]))

fig4 = plt.figure(4)
axFP = fig4.add_subplot(1, 1, 1)
footprint.draw_footprint(Qxy_fp, axis_object=axFP, linewidth = 1)
axFP.set_xlim(.1, .16)
axFP.set_ylim(.18, .25)
axFP.set_aspect('equal')
fig4.suptitle(mode)
plt.show()
