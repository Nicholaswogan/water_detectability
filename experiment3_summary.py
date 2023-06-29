import numpy as np
import pickle
from rfast import detection_sigma

def get_filename(root_dir, T_surf, SNR, fCH4):
    filename = 'Ts='+('%.5f'%(T_surf))+'_SNR='+('%.5f'%(SNR))+'_fCH4='+('%.5e'%(fCH4))
    filename = root_dir + "/" + filename
    return filename

def write_summary(root_dir, outfile, T_surf, SNRs_, fCH4s_):

    sol = {}

    for cc in fCH4s_:
        sol[cc] = {}
        for ss in SNRs_:
            tmp = {}
            filename = get_filename(root_dir, T_surf, ss, cc)

            with open(filename+'_data.pkl','rb') as f:
                results = pickle.load(f)
            tmp['data'] = results

            with open(filename+'_all.pkl','rb') as f:
                results = pickle.load(f)
            tmp['all_evidence'] = results['logz'][-1]

            with open(filename+'_noCH4.pkl','rb') as f:
                results = pickle.load(f)
            tmp['noCH4_evidence'] = results['logz'][-1]

            # detection significance
            lnB_CH4 = tmp['all_evidence'] - tmp['noCH4_evidence']
            tmp['sig_CH4'] = detection_sigma(lnB_CH4)

            sol[cc][ss] = tmp

            print(cc, ss)

    with open(outfile,'wb') as f:
        pickle.dump(sol,f)
        
def summary_experiment3():
    root_dir = "results/experiment3"
    outfile = "results/experiment3/experiment3_summary.pkl"

    T_surf = 288.0
    SNRs_ = np.arange(2.5,40.1,2.5)
    fCH4s_ = np.arange(0.05,1.0001,0.05)/100
    write_summary(root_dir, outfile, T_surf, SNRs_, fCH4s_)
    
if __name__ == "__main__":
    summary_experiment3()
