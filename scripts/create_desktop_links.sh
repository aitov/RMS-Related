#!/bin/bash

DIR=$(pwd)
# Get full path of Desktop
DESKTOP=$(realpath ~/Desktop)

# Create links to scripts, so they can be updated
ln -sf $DIR/start_copy_required_fits.sh $DESKTOP/.
ln -sf $DIR/start_processing.sh $DESKTOP/.
ln -sf $DIR/start_sky_fit2_processing.sh $DESKTOP/.

