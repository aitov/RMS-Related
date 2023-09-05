# Raspberry Pi
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  source ~/vRMS/bin/activate
  rms_folder=~/source/RMS
  home_folder=/home
elif [[ "$OSTYPE" == "darwin"* ]]; then
  # Mac Apple Silicon
  if [[ $(uname -m) == 'arm64' ]]; then
    source ~/.conda/envs/rms/bin/activate
  # Mac Intel
  elif [[ $(uname -m) == 'x86_64' ]]; then
    source ~/anaconda3/envs/rms/bin/activate
  fi
  rms_folder=~/home/projects/RMS
  home_folder=~/home
fi