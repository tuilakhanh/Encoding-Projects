#!/usr/bin/env python3
import os

import lvsfunc as lvf
from acsuite import eztrim


path = r'BDMV/かぐや様は告らせたい Vol.5/BD/BDMV/STREAM/00001.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, -25), f"{os.path.splitext(path)[0]}.wav", f"{__file__[:-3]}_cut.wav")
