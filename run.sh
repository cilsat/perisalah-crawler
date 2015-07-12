#!/bin/bash

cd `dirname $0`
source '/home/inti/.virtualenvs/perisalah-crawler/bin/activate'
python3 "${@:1}"
