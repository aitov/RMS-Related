# Inits variables and activates python env
# For execution on RMS Raspberry Pi - no need do additional action - used default values
# For local execution : required variables could be overriden by local paths
# Use local.properties.template file as example, override required properties and copy it with name : local.properties

# Default properties for Raspberry Pi
venv=~/vRMS
rms_folder=~/source/RMS
bin_viewer_folder=~/source/cmn_binviewer
home_folder=/home

if [ -e "local.properties" ]; then
  source "local.properties"
fi

source "$venv/bin/activate"
