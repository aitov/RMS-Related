#!/bin/bash
. activate.sh

IFS=',' read -ra ssh_hosts_list <<< "$ssh_hosts"

# Check which hosts are online and build a list of available hosts
available_ssh_hosts_list=()
for ssh_host in "${ssh_hosts_list[@]}"; do
  # Parse user_host and port if present
  if [[ "$ssh_host" == *:* ]]; then
    user_host="${ssh_host%%:*}"
    ssh_port="${ssh_host##*:}"
    ssh_cmd=(ssh -o ConnectTimeout=3 -o BatchMode=yes -o StrictHostKeyChecking=no -p "$ssh_port" "$user_host" "exit")
  else
    user_host="$ssh_host"
    ssh_cmd=(ssh -o ConnectTimeout=3 -o BatchMode=yes -o StrictHostKeyChecking=no "$user_host" "exit")
  fi
  "${ssh_cmd[@]}" 2>/dev/null
  if [ $? -eq 0 ]; then
    available_ssh_hosts_list+=("$ssh_host")
    echo "Host $ssh_host is online."
  else
    echo "Host $ssh_host is offline or unreachable, skipping."
  fi
done

if [ ${#available_ssh_hosts_list[@]} -eq 0 ]; then
  echo "No available SSH hosts found. Exiting."
  exit 1
fi

for ssh_host in "${available_ssh_hosts_list[@]}"; do
  cd "$rms_related_folder/scripts"
  if [ "$automatic_processing" = "true" ]; then
    . start_automatic_tar_processing.sh
  else
    . start_tar_processing.sh
  fi
done
