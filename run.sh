#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")"

. ./env/bin/activate
exec python beaconrelay.py
