# Repository of scripts to make input files for the cicero-scm climate model

## This is the version as used in RCMIP phases I and II
To get the RCMIP phases I and II versions use checkout tag v0.0.0-RCMIPI

It is built to deal with and convert RCMIP format files from these
two phases into emissions concentrations and forcing files for the version of 
the ciceroscm used for these RCMIP phases (and the AR6 process) and is
compatible with both the fortran version of ciceroscm used for these and
the python version up to version v1.2.0 
(https://github.com/ciceroOslo/ciceroscm/releases/tag/v1.2.0)

Code is neither elegant nor efficient, and was originally written in python2 
(though should be mostly python3 compatible), 
using a very limited and fairly standard number of libraries, with all the
caveats that entails.

For more updated versions of interpolation compatible with newer
versions of ciceroscm, checkout a newer version of the repository.

## Usage

### `make_scenario_files_RCMIP.py`
This script is used to read in and convert RCMIP emissions data to ciceroscm data
Specify in the top of the __main__ block which scenarios (and rcp sceanrios) that 
you want to convert or leave open and all scenarios in the datafile will be processed. Then a gaspamfile is used to find the components and units 
that need to be read from rcmip formatted csv. This data is read, converted to 
appropriate units and linearly interpolated to missing years. Finally a formatted
file is printed for each scenario.

### `make_scenario_files_IAMC.py`
This script is used to read in and convert newer scenariomip IAMC data to ciceroscm data
Specify in the top of the __main__ block which scenarios that 
you want to convert or leave open and all scenarios in the datafile will be processed. Then a gaspamfile is used to find the components and units 
that need to be read from rcmip formatted csv. This data is read, converted to 
appropriate units and linearly interpolated to missing years. Finally a formatted
file is printed for each scenario.

### `make_concentration_files_RCMIP.py`
This script is used to read in and convert RCMIP concentrations data to ciceroscm data
Specify in the top of the __main__ block which scenarios (and rcp sceanrios) that 
you want to convert or leave open and all scenarios in the datafile will be processed. Then a gaspamfile is used to find the components and units 
that need to be read from rcmip formatted csv. This data is read, converted to 
appropriate units and linearly interpolated to missing years. Finally a formatted
file is printed for each scenario.


### `make_concentration_files_IGCC.py`
This script is used to read in and convert IGCC concentrations data to ciceroscm data
Specify in the top of the __main__ a possible ssp-file to fudge the data with into the future, otherwise the file will stop where the igcc datafile stops. Then a gaspamfile is used to find the components and units 
that need to be read from igcc formatted csv. This data is read, converted to 
appropriate units and linearly interpolated to missing years. Finally a formatted
file is printed for each scenario.

### `make_RF_files_RCMIP.py`
This script is used to read in and convert RCMIP forcing data for Solar, Volcanic and 
Land Use Albedo change data to ciceroscm compatible data formats for these.
Specify in the top of the __main__ block which scenarios (and rcp sceanrios) that 
you want to convert from rcmip formatted csvs. This data is read, converted and 
linearly interpolated to missing years. Finally a formatted
files are printed for each scenario and forcing type specified.

### `make_RF_files_IGCC.py`
This script is used to read in and convert IGCC forcing data for Solar, Volcanic and 
Land Use Albedo change data to ciceroscm compatible data formats for these.

### `make_input_w_regional_aerosol.py`
Is a supplement to  `make_scenario_files_RCMIP.py`, which can take an existing
emissions file for a scenario outputted by the  `make_scenario_files_RCMIP.py`
script and make a new version which also includes regionally split emissions
for BC, OC and Sulfur. This script is newer and requires the pandas library in
a relatively recent iteration (post python >= 3.9 and compatible pandas)

### `interpolation_of_input.py`
This provides a very rudimentary and inefficent implementation of linear
interpolation which is used in some of the other scripts. If you are looking
at a newer version of this repository (v>1) and you still see this section here
someone has not done their job.

### `misc_utils.py`
Collection of various shared functionality, like component name mapping, unit conversion etc.


This repository was built to work with input data from
* RCMIP: 10.5281/zenodo.4589726.
* IGCC: https://doi.org/10.5281/zenodo.15639576
