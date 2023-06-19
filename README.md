```sh

mamba create -n rfast -c conda-forge python numpy numba scipy ruamel.yaml astropy emcee dynesty scikit-build cmake ninja cython h5py matplotlib jupyter multiprocess

mamba activate rfast

git clone --recursive https://github.com/Nicholaswogan/rfast.git
cd rfast
git checkout b9e5bc8cb27770448fd998b0ce66ebdf13ec4ea3
python -m pip install --no-deps --no-build-isolation . -v
cd ..
rm -rf rfast

git clone --recursive https://github.com/Nicholaswogan/clima
cd clima
git checkout e3675ac09896d5ed06e478c935ebbaad94ebd83f
python -m pip install --no-deps --no-build-isolation . -v
cd ..
rm -rf clima
```