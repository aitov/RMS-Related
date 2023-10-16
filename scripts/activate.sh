# Inits variables and activates python env
# For execution on RMS Raspberry Pi - no need do additional action - used default values
# For local execution : required variables could be overriden by local paths
# Use local.properties.template file as example, override required properties and copy it with name : local.properties

# Default properties for Raspberry Pi
venv=~/vRMS
rms_folder=~/source/RMS
bin_viewer_folder=~/source/cmn_binviewer
home_folder=/home
rms_related_folder=~/source/RMS-Related

if [ -e "local.properties" ]; then
  source "local.properties"
fi

source "$venv/bin/activate"

create_folder() {

  if [ -z "$1" ]; then
    echo "Please specify folder name"
    read -n 1 -s -r -p "Press any key to exit"
    echo
    exit
  fi

  if [ ! -d "$1" ]; then
    mkdir -p "$1"
  fi
}

delete_folder() {
   if [ -z "$1" ]; then
      echo "Please specify folder name"
      read -n 1 -s -r -p "Press any key to exit"
      echo
      exit
  fi

  if [ -d "$1" ]; then
    rm -r "$1"
  fi
}


delete_file() {
   if [ -z "$1" ]; then
      echo "Please specify file name"
      read -n 1 -s -r -p "Press any key to exit"
      echo
      exit
  fi

  if [ -f "$1" ]; then
    rm "$1"
  fi
}
