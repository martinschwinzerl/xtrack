import numpy as np

import xobjects as xo
import xtrack as xt

import xline

context = xo.ContextCpu()
context = xo.ContextCupy()
#context = xo.ContextPyopencl()

x_aper_min = -0.1
x_aper_max = 0.2
y_aper_min = 0.2
y_aper_max = 0.3

part_gen_range = 0.35
n_part=10000

pyst_part = xline.Particles(
        p0c=6500e9,
        x=np.random.uniform(-part_gen_range, part_gen_range, n_part),
        px = np.zeros(n_part),
        y=np.random.uniform(-part_gen_range, part_gen_range, n_part),
        py = np.zeros(n_part),
        sigma = np.zeros(n_part),
        delta = np.zeros(n_part))

part_dict = xt.pyparticles_to_xtrack_dict(pyst_part)
particles = xt.Particles(_context=context, **part_dict)

aper_pyst = xline.elements.LimitRect(min_x=x_aper_min,
                                          max_x=x_aper_max,
                                          min_y=y_aper_min,
                                          max_y=y_aper_max)

aper = xt.LimitRect(_context=context,
                    **aper_pyst.to_dict())
aper.track(particles)

aper_pyst.track(pyst_part)

part_id = context.nparray_from_context_array(particles.particle_id)
part_state = context.nparray_from_context_array(particles.state)
part_x = context.nparray_from_context_array(particles.x)
part_y = context.nparray_from_context_array(particles.y)

id_alive = part_id[part_state>0]

assert np.allclose(pyst_part.partid, id_alive)

import matplotlib.pyplot as plt
plt.close('all')
plt.figure(1)
plt.plot(part_x, part_y, '.', color='red')
plt.plot(part_x[part_state>0], part_y[part_state>0], '.', color='green')

plt.show()
