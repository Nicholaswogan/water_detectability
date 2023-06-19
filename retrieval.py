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

def CO2_T_trop_guess(distance_au):
    distances_au = np.array([1.  , 1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09, 1.1 ,
       1.11, 1.12, 1.13, 1.14, 1.15, 1.16, 1.17, 1.18, 1.19, 1.2 , 1.21,
       1.22, 1.23, 1.24, 1.25, 1.26, 1.27, 1.28, 1.29, 1.3 , 1.31, 1.32,
       1.33, 1.34, 1.35, 1.36, 1.37, 1.38, 1.39, 1.4 , 1.41, 1.42, 1.43,
       1.44, 1.45, 1.46, 1.47, 1.48, 1.49, 1.5 ])
    N_CO2s = np.array([2.10129270e-02, 5.00923877e-02, 1.07593109e-01, 2.06253691e-01,
       3.59126589e-01, 5.78659830e-01, 8.74196621e-01, 1.25404809e+00,
       1.72819834e+00, 2.30704292e+00, 2.99769689e+00, 3.80252669e+00,
       4.71498985e+00, 5.72299342e+00, 6.81169536e+00, 7.96616404e+00,
       9.17723097e+00, 1.04402096e+01, 1.17543465e+01, 1.31183000e+01,
       1.45361496e+01, 1.60205906e+01, 1.75797619e+01, 1.92202823e+01,
       2.09507244e+01, 2.27819371e+01, 2.47217606e+01, 2.67751216e+01,
       2.89523441e+01, 3.12659538e+01, 3.37193453e+01, 3.63303457e+01,
       3.90990266e+01, 4.20306398e+01, 4.51147330e+01, 4.83475434e+01,
       5.17302989e+01, 5.52788994e+01, 5.90503190e+01, 6.30917726e+01,
       6.74772385e+01, 7.21709757e+01, 7.72089247e+01, 8.26470296e+01,
       8.84927457e+01, 9.48711202e+01, 1.01918242e+02, 1.09593176e+02,
       1.18012480e+02, 1.27330771e+02, 1.37822249e+02])
    T_trops = np.array([219.62574385, 218.57005786, 217.53007578, 216.50185542,
       215.47779685, 214.45104632, 213.41943804, 212.38332992,
       211.34234676, 210.29508998, 209.24081381, 208.18056032,
       207.11638257, 206.05123347, 204.98844747, 203.93157649,
       202.88220304, 201.8416212 , 200.81009418, 199.78825018,
       198.77533446, 197.76996023, 196.77078039, 195.77771469,
       194.79027983, 193.80737126, 192.82813614, 191.85321382,
       190.88200758, 189.91355995, 188.94814441, 187.98501996,
       187.0247644 , 186.0665982 , 185.11292833, 184.16479327,
       183.2220666 , 182.28417286, 181.34777824, 180.4103635 ,
       179.46812673, 178.52527112, 177.58068422, 176.63146804,
       175.68017496, 174.72156536, 173.75059281, 172.77308102,
       171.78597458, 170.78568178, 169.76471886])
    
    ind = np.argmin(np.abs(distances_au - distance_au))
    N_CO2_guess = N_CO2s[ind]
    T_trop_guess = T_trops[ind]
    return N_CO2_guess, T_trop_guess

def spawn_retrieval(save_dir,
                    c, N_i, distance_au, T_surf,
                    SNR, FpFs_err):

    filename = save_dir+'/'+'AU='+('%.5f'%(distance_au))+'_SNR='+('%.5f'%(SNR))

    # get guess
    N_CO2_guess, T_trop_guess = CO2_T_trop_guess(distance_au)

    # make fake data
    dat, err = utils.make_data(c, N_i, distance_au, T_surf, N_CO2_guess, T_trop_guess, \
                               TEMPLATE_FILENAME, SNR, FpFs_err)
    
    # save the data
    sol = {}
    sol['lam'] = r.lam
    sol['dlam'] = r.dlam
    sol['dat'] = dat
    sol['err'] = err
    sol['distance_au'] = distance_au
    sol['SNR'] = SNR
    with open(filename+'_data.pkl','wb') as fil:
        pickle.dump(sol, fil)

    # change the distance_au for retrieval
    ind = list(GENSPEC_INPUTS).index('a')
    r.scr_genspec_inputs[ind] = distance_au

    r.nested_process(dat, err, filename+'_all.pkl')

    r.remove_gas('h2o')
    r.nested_process(dat, err, filename+'_noH2O.pkl')
    r.undo_remove_gas()

def spawn_all_retrievals(save_dir, 
                         c, N_i, distances_au, T_surf, 
                         SNRs, FpFs_err,
                         max_processes):

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

        # if retrievals are less than max process,
        # then spawn
        if ii < len(SNRs) and nr < max_processes-2:
            spawn_retrieval(save_dir,
                            c, N_i, distances_au[ii], T_surf,
                            SNRs[ii], FpFs_err)
            ii+=1

        finish = time.time()
        tot_time = (finish-start)/60

        # print progress
        fmt = "{:20}"
        print(fmt.format("running: "+'%i'%nr)+\
        fmt.format('completed: ''%i'%nc)+\
        fmt.format('total: ''%i'%nt)+\
        "{:30}".format('time: ''%.2f'%tot_time+' min'),end='\r')
        
        time.sleep(1)

def experiment1():
    save_dir = "results/experiment1"
    max_processes = 5

    # This is the "signal"
    FpFs_err = 3.55e-10

    # Make clima object
    c = AdiabatClimate('input/species.yaml',
                  'input/settings.yaml',
                  'input/Sun_now.txt')
    c.P_top = 1.0
    c.RH = np.ones(len(c.species_names))*0.8
    c.rad.surface_albedo = 0.22
    c.use_make_column_P_guess = False

    # Surface temperature
    T_surf = 288.0

    # Gases other than CO2
    N_i = np.array([10.0e3, 400.0e-6*23, 36.0*1])

    # SNR and distances to consider
    SNRs_ = np.arange(2.5,40.1,2.5)
    distances_au_ = np.array([1.0, 1.2, 1.4, 1.6, 1.8])

    SNRs = []
    distances_au = []
    for ss in SNRs_:
        for dd in distances_au_:
            SNRs.append(ss)
            distances_au.append(dd)

    spawn_all_retrievals(save_dir, 
                         c, N_i, distances_au, T_surf, 
                         SNRs, FpFs_err,
                         max_processes)
    
if __name__ == '__main__':
    experiment1()

    



            


    
