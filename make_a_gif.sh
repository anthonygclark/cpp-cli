#!/bin/bash

[[ -z $1 ]] && {
    echo "\$1 - output gif name"
    exit 1
}

palette="/tmp/palette.png"
rate=15
filters="fps=${rate},scale=500:-1:flags=lanczos"

ffmpeg -video_size 640x480 -framerate ${rate} -f x11grab -i :0.0+100,200 output.mp4

ffmpeg -v warning -i output.mp4 -vf "$filters,palettegen" -y $palette
ffmpeg -v warning -i output.mp4 -i $palette -lavfi "$filters [x]; [x][1:v] paletteuse" -y $1
