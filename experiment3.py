import numpy as np
import pickle
import os
import time

from clima import AdiabatClimate
import rfast
from rfast.objects import GENSPEC_INPUTS

import utils

# global instance of rfast
TEMPLATE_FILENAME = 'input/inputs.scr'
r = rfast.Rfast(TEMPLATE_FILENAME)
r.initialize_retrieval("input/rpars.txt")

def spawn_retrieval(save_dir,
                    c, T_surf, fCH4, f_i, P_surf, bg_gas,
                    SNR, FpFs_err, tmp_atmosphere_outfile, tmp_scr_outfile):

    filename = save_dir+'/'+'Ts='+('%.5f'%(T_surf))+'_SNR='+('%.5f'%(SNR))

    f_i[c.species_names.index('CH4')] = fCH4
    P_i = f_i*P_surf
    P_i[c.species_names.index('H2O')] = 200e6

    # make fake data
    dat, err = utils.make_data_temperature_experiment(c, T_surf, P_i, P_surf, bg_gas, 
                                                      TEMPLATE_FILENAME, SNR, FpFs_err,
                                                      tmp_atmosphere_outfile, tmp_scr_outfile)
    
    # save the data
    sol = {}
    sol['lam'] = r.lam
    sol['dlam'] = r.dlam
    sol['dat'] = dat
    sol['err'] = err
    sol['T_surf'] = T_surf
    sol['SNR'] = SNR
    with open(filename+'_data.pkl','wb') as fil:
        pickle.dump(sol, fil)

    r.nested_process(dat, err, filename+'_all.pkl')

    r.remove_gas('ch4')
    r.nested_process(dat, err, filename+'_noCH4.pkl')
    r.undo_remove_gas()

def spawn_all_retrievals(save_dir, 
                         c, T_surf, fCH4s, f_i, P_surf, bg_gas, 
                         SNRs, FpFs_err,
                         max_processes, tmp_atmosphere_outfile, tmp_scr_outfile):

    if not os.path.isdir(save_dir):
        raise Exception(save_dir+' must exist!')

    start = time.time()
    
    # while we still have models to run
    nt = len(SNRs)*2
    ii = 0
    while True:

        # check how many retrievals are running
        nr = 0
        nc = 0
        for process in r.retrieval_processes:
            if process['process'].is_alive():
                nr+=1
            else:
                nc+=1
                
        if nc == nt:
            # break if we have completed all processes
            break

        # if retrievals are less than max process, then spawn
        if ii < len(SNRs) and nr < max_processes-2:
            spawn_retrieval(save_dir,
                            c, T_surf, fCH4s[ii], f_i, P_surf, bg_gas,
                            SNRs[ii], FpFs_err,
                            tmp_atmosphere_outfile, tmp_scr_outfile)
            ii+=1

        finish = time.time()
        tot_time = (finish-start)/60

        # print progress
        fmt = "{:20}"
        print(fmt.format("running: "+'%i'%nr)+\
        fmt.format('completed: ''%i'%nc)+\
        fmt.format('total: ''%i'%nt)+\
        "{:30}".format('time: ''%.2f'%tot_time+' min'),end='\n')
        
        time.sleep(5)

def experiment3():
    save_dir = "results/experiment3"
    max_processes = 40
    tmp_atmosphere_outfile = 'tmp12345_atmosphere_exp3.txt'
    tmp_scr_outfile = 'tmp12345_exp3.scr'
    
    # This is the "signal"
    FpFs_err = 3.55e-10

    # Make clima object
    c = AdiabatClimate('input/species.yaml',
                  'input/settings.yaml',
                  'input/Sun_now.txt')
    c.use_make_column_P_guess = False
    c.P_top = 1.0
    c.RH = np.ones(len(c.species_names))*0.8
    c.T_trop = 215
    c.rad.surface_albedo = 0.24

    # Atmospheric composition
    f_i = np.array([1.0, 0.01, 1.0, 1.0e-6, 0.001])
    P_surf = 1.035e6
    bg_gas = 'N2'
    T_surf = 288.0

    # parameter space
    SNRs_ = np.arange(2.5,40.1,2.5)
    fCH4s_ = np.arange(0.05,1.0001,0.05)/100

    SNRs = []
    fCH4s = []
    for ss in SNRs_:
        for cc in fCH4s_:
            SNRs.append(ss)
            fCH4s.append(cc)

    spawn_all_retrievals(save_dir, 
                         c, T_surf, fCH4s, f_i, P_surf, bg_gas, 
                         SNRs, FpFs_err,
                         max_processes, tmp_atmosphere_outfile, tmp_scr_outfile)
    
if __name__ == '__main__':
    experiment3()

    



            


    
