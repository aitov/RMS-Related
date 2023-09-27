DIR=$(dirname $0)
DIR=$(realpath $DIR)
# Get full path of Desktop
DESKTOP=$(realpath ~/Desktop)

# Create links to scripts, so they can be updated
ln -sf $DIR/start_copy_required_fits.sh $DESKTOP/.
ln -sf $DIR/start_processing.sh $DESKTOP/.

