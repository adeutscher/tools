#!/bin/bash

# A script for storing a data payload in an index file located at ~/.local/hash_index.dat
# The goal of this was to help to support a system of updates files in the same manner
#  that is currently applied to SSH configurations by storing checksums.
#
# The 'update-dotfile.sh' script ended up adopting the SSH configuration pattern so completely
#   that this script became obselete before it was even commited. However, I am keeping
#   it around in case it becomes useful for supporting another system in the future.
#
# Content format:
#   key|update-timestamp|data

# Usage
#
#  To get the data for an index:
#     ./hash-index.sh key
#  To also set the data for an index as well as retrieve the original value:
#     ./hash-index.sh key data

INDEX_FILE="${HOME}/.local/hash-index.dat"

KEY="${1}"
NEW_DATA="${2}"

# If no key given, then there is no point continuing.
[ -z "${KEY}" ] && exit 1

# Get the hash, ignoring minor errors like "file not found"
DATA="$(grep "^${KEY}|" "${INDEX_FILE}" 2> /dev/null | cut -d'|' -f 3-)"

if [ -n "${NEW_DATA}" ] && [[ "${NEW_DATA}" != "${DATA}" ]]; then
  # New hash is different from stored one, update.
  sed -r -i "/^${KEY}\|/d" "${INDEX_FILE}" 2> /dev/null
  mkdir -p "${INDEX_FILE%/*}" # Create directory
  printf "%s|%d|%s\n" "${KEY}" "$(date +%s)" "${NEW_DATA}" >> "${INDEX_FILE}"
fi

# Print out the old data.
echo "${DATA}"
