#!/bin/bash

# Save PID
pid=$$
pgid=$(ps -o pgid= -p "$pid")

echo $pgid > $HOME/trust-me-setup/tmp/startup_script.pid

source "$HOME/miniconda3/etc/profile.d/conda.sh"
echo $(conda --version)

# Define centralized username for all data collection
USERNAME=${1:-"TESTING"}
echo "Using username: $USERNAME"

# Define base path
BASE_PATH="$HOME/trust-me-setup"

# Create username file that will be read by all scripts
echo "$USERNAME" > "$BASE_PATH/tmp/current_username"

while [ ! -e /dev/video0 ];
do
  echo "Waiting for /dev/video0..."
  sleep 5
done

echo "Video now available. Starting script..."

if ! conda info > /dev/null 2>&1; 
then
  echo "Initializing conda"
  conda init
  exec bash
fi

cd "$BASE_PATH"

# Paths
TOBII_PATH="$BASE_PATH/installers/tobii/run_tobii.sh";
RGB_PATH="$BASE_PATH/installers/data_capture/capture_data.py";
STREAMDECK_PATH="$BASE_PATH/installers/streamdeck/run_streamdeck.py";

# Activate environment
conda activate tobii #recording

if [ ! -f "$TOBII_PATH" ];
then
  echo "Error! Tobii script not found at $TOBII_PATH"
  exit 1
fi

if [ ! -f "$RGB_PATH" ];
then
  echo "Error! RGB script not found at $RGB_PATH"
  exit 1
fi

chmod +x "$TOBII_PATH"

python "$BASE_PATH/installers/data_capture/auto_config_hw.py"

# Run process in background
python "$RGB_PATH" -n "$USERNAME" &
echo "Started recording RGB"

# Run process in background
"$TOBII_PATH" "$USERNAME" "$BASE_PATH" &
echo "Started recording tobii"

# Run process in background
python "$STREAMDECK_PATH" "$USERNAME" "$BASE_PATH" &
echo "Streamdeck running"

wait
echo "Done"
