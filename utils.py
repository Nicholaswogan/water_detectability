import numpy as np
from scipy import optimize

from rfast import Rfast

def equilibrium_temperature(stellar_radiation, bond_albedo):
    sigma_si = 5.670374419e-8
    return ((stellar_radiation*(1.0 - bond_albedo))/(4.0*sigma_si))**(0.25)

def skin_temperature(stellar_radiation, bond_albedo):
    return equilibrium_temperature(stellar_radiation, bond_albedo)*(0.5)**(0.25)

def objective(x, c, N_i, distance_au, T_surf):
    log10_N_CO2, log10_T_trop = x
    N_CO2 = 10.0**log10_N_CO2
    T_trop = 10.0**log10_T_trop
    
    # set T_trop
    c.T_trop = T_trop
    
    # compute solar scaling
    solar_scaling = (1/distance_au)**2
    
    # Set CO2
    N_i[c.species_names.index('CO2')] = N_CO2
    
    # radiative transfer
    ISR, OLR = c.TOA_fluxes_column(T_surf, N_i)
    ISR = ISR*solar_scaling # rescale solar flux to distance from sun
    
    # compute the skin temperature
    bond_albedo = c.rad.wrk_sol.fup_n[-1]/c.rad.wrk_sol.fdn_n[-1] # bond albedo
    total_solar_energy = solar_scaling*(4*c.rad.wrk_sol.fdn_n[-1]/1e3) # Total solar energy (W/m^2)
    T_skin = skin_temperature(total_solar_energy, bond_albedo) # skin temperature
    
    # residual
    fvec = np.empty(2)
    fvec[0] = OLR - ISR
    fvec[1] = T_skin - T_trop
    
    return fvec

def find_CO2_for_stable_climate(c, N_i, distance_au, T_surf, N_CO2_guess, T_trop_guess):
    args = (c, N_i, distance_au, T_surf)
    initial_guess = np.log10(np.array([N_CO2_guess, T_trop_guess]))

    sol = optimize.root(objective, initial_guess, args=args, method='hybr')
    if not sol.success or c.T_trop < 100.0:
        raise Exception('root solve failed')
    fvec = objective(sol.x, c, N_i, distance_au, T_surf)
    
    N_CO2, T_trop = 10.0**(sol.x)
    
    return N_CO2

def rewrite_clima_atmosphere(c, tmp_atmosphere_outfile, rfast_species):
    
    # species in rfast that are not in clima
    missing_species = []
    for sp in rfast_species:
        if sp not in c.species_names:
            missing_species.append(sp)
    
    # open atmosphere file
    with open(tmp_atmosphere_outfile,'r') as f:
        lines = f.readlines()
    
    # Add rfast species to labels
    fmt = '{:27}'
    labels_line = lines[0].strip('\n')
    for sp in missing_species:
        labels_line+=fmt.format(sp)
    labels_line+='\n'

    # Add rfast species to atmosphere file at small concentrations
    new_lines = []
    for line in lines[1:]:
        tmp = line.strip('\n')+'   '
        for i,sp in enumerate(missing_species):
            tmp+=fmt.format('%.1e'%(1.0e-50))
        tmp+='\n'
        new_lines.append(tmp)
    
    # Write the new atmosphere file
    with open(tmp_atmosphere_outfile,'w') as f:
        f.write(labels_line)
        for line in new_lines:
            f.write(line)
    
    # get labels of atmosphere file for later use
    labels = labels_line.split()
    
    return labels

def make_rfast_from_clima(template_filename, c, distance_au, 
                          tmp_atmosphere_outfile='tmp12345_atmosphere.txt', 
                          tmp_scr_outfile='tmp12345.scr'):

    # Write clima file
    c.out2atmosphere_txt(tmp_atmosphere_outfile, eddy=np.zeros(c.z.shape[0]), overwrite=True)

    # read template file
    with open(template_filename,'r') as f:
        lines = f.readlines()

    # keys we we need to find
    keys = [
        'pmax ',
        'species_r ',
        'rdgas ',
        'fnatm ',
        'skpatm ',
        'colr ',
        'colpr ',
        'psclr ',
        'imix ',
        't0 ',
        'rdtmp ',
        'fntmp ',
        'skptmp ',
        'colt ',
        'colpt ',
        'psclt ',
        'a '
    ]
    
    # check keys exist in the file
    i = 0
    for key in keys:
        for line in lines:
            if line.startswith(key):
                i+=1
                break
    if i != len(keys):
        raise Exception('Can not find key in template scr file.')
    
    # get rfast species
    for line in lines:
        if line.startswith('species_r '):
            a = line.split('#')[0].split('=')[1].strip().split(',')
            rfast_species = [b.upper() for b in a]
            break

    # rewrite atmosphere file so it works well with rfast
    clima_file_labels = rewrite_clima_atmosphere(c, tmp_atmosphere_outfile, rfast_species)
    
    # change file to match what is in clima
    new_lines = []
    for line in lines:
        new_line = line
        if line.startswith('pmax '):
            new_line = 'pmax = %.5e\n'%(((c.P_surf/1e6)*1e5))
        if line.startswith('species_r '):
            a = line.split('#')[0].split('=')[1].strip().split(',')
            rfast_species = [b.upper() for b in a]
            colr_list = [clima_file_labels.index(b)+1 for b in rfast_species]
            colr = ','.join(['%i'%b for b in colr_list])
        if line.startswith('rdgas '):
            new_line = 'rdgas = True\n'
        if line.startswith('fnatm '):
            new_line = 'fnatm = '+tmp_atmosphere_outfile+'\n'
        if line.startswith('skpatm '):
            new_line = 'skpatm = 1\n'
        if line.startswith('colr '):
            new_line = 'colr = '+colr+'\n'
        if line.startswith('colpr '):
            new_line = 'colpr = 2\n'
        if line.startswith('psclr '):
            new_line = 'psclr = 1.0e5\n'
        if line.startswith('imix '):
            new_line = 'imix = 0\n'
        if line.startswith('t0 '):
            new_line = 't0 = %.1f\n'%(c.T_surf)
        if line.startswith('rdtmp '):
            new_line = 'rdtmp = True\n'
        if line.startswith('fntmp '):
            new_line = 'fntmp = '+tmp_atmosphere_outfile+'\n'
        if line.startswith('skptmp '):
            new_line = 'skptmp = 1\n'
        if line.startswith('colt '):
            new_line = 'colt = 4\n'
        if line.startswith('colpt '):
            new_line = 'colpt = 2\n'
        if line.startswith('psclt '):
            new_line = 'psclt = 1.0e5\n'
        if line.startswith('a '):
            new_line = 'a = %.6f\n'%(distance_au)

        new_lines.append(new_line)

    # write the new file
    with open(tmp_scr_outfile,'w') as f:
        for line in new_lines:
            f.write(line)
            
    r = Rfast(tmp_scr_outfile)
    return r

def make_data(c, N_i, distance_au, T_surf, N_CO2_guess, T_trop_guess, 
              template_filename, SNR, FpFs_err):

    # Find stable climate
    N_CO2 = find_CO2_for_stable_climate(c, N_i, distance_au, T_surf, N_CO2_guess, T_trop_guess)

    # make rfast from clima results
    r = make_rfast_from_clima(template_filename, c, distance_au)

    # compute the spectrum
    F1, F2 = r.genspec_scr()

    # set SNR and generate data
    assert r.scr.snr0.shape[0] == 1 
    r.scr.snr0 = np.array([SNR])
    dat, err = r.noise_at_FpFs(F2, FpFs_err)

    return dat, err