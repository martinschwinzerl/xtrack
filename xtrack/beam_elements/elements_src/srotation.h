#ifndef XTRACK_SROTATION_H
#define XTRACK_SROTATION_H

/*gpufun*/
void SRotation_track_local_particle(SRotationData el, LocalParticle* part){

    int64_t const n_part = LocalParticle_get_num_particles(part); 
    for (int ii=0; ii<n_part; ii++){ //only_for_context cpu_serial cpu_openmp
	part->ipart = ii;            //only_for_context cpu_serial cpu_openmp

    	double const sin_z = SRotationData_get_sin_z(el);
    	double const cos_z = SRotationData_get_cos_z(el);

    	double const x  = LocalParticle_get_x(part);
    	double const y  = LocalParticle_get_y(part);
    	double const px = LocalParticle_get_px(part);
    	double const py = LocalParticle_get_py(part);

    	double const x_hat  =  cos_z * x  + sin_z * y;
    	double const y_hat  = -sin_z * x  + cos_z * y;

    	double const px_hat =  cos_z * px + sin_z * py;
    	double const py_hat = -sin_z * px + cos_z * py;


    	LocalParticle_set_x(part, x_hat);
    	LocalParticle_set_y(part, y_hat);

    	LocalParticle_set_px(part, px_hat);
    	LocalParticle_set_py(part, py_hat);
    } //only_for_context cpu_serial cpu_openmp

}

#endif
