#!/usr/bin/env bash
# sanity check helper script to make sure i can iterate with ingestSip.py
# https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" 
INPUT_DIR="${1}"
cd "$INPUT_DIR"
for filename in *; do
	echo $filename
	/usr/bin/python3 "$DIR/ingestSip.py" "-i" "$filename" "-u" "mcq"
done
