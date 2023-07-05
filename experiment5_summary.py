import numpy as np
import pickle
from rfast import detection_sigma

def get_filename(root_dir, T_surf, SNR):
    filename = 'Ts='+('%.5f'%(T_surf))+'_SNR='+('%.5f'%(SNR))
    filename = root_dir + "/" + filename
    return filename

def write_summary(root_dir, outfile, SNRs_, T_surf):

    sol = {}
    for ss in SNRs_:
        tmp = {}
        filename = get_filename(root_dir, T_surf, ss)

        with open(filename+'_data.pkl','rb') as f:
            results = pickle.load(f)
        tmp['data'] = results

        with open(filename+'_all.pkl','rb') as f:
            results = pickle.load(f)
        tmp['all_evidence'] = results['logz'][-1]

        with open(filename+'_noH2O.pkl','rb') as f:
            results = pickle.load(f)
        tmp['noH2O_evidence'] = results['logz'][-1]

        # detection significance
        lnB_H2O = tmp['all_evidence'] - tmp['noH2O_evidence']
        tmp['sig_H2O'] = detection_sigma(lnB_H2O)

        sol[ss] = tmp

    with open(outfile,'wb') as f:
        pickle.dump(sol,f)
        
def summary_experiment5():
    root_dir = "results/experiment5"
    outfile = "results/experiment5/experiment5_summary.pkl"

    SNRs_ = np.arange(2.5,40.1,2.5)
    write_summary(root_dir, outfile, SNRs_, 288)
    
if __name__ == "__main__":
    summary_experiment5()
