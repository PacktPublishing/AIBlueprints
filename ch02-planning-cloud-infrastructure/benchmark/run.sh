#!/bin/sh

taskids=$*

mkdir -p images
for taskid in $taskids
do
    mkdir -p images/$taskid
    aws s3 cp s3://smartcode/pan-starrs1 images/$taskid --recursive --exclude "*" --include "rings.v3.skycell.$taskid.*.png"
    parallel ./cpubenchmark {} ::: images/$taskid/*
    rm -rf images/$taskid
done


