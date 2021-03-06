#!/usr/bin/env python3
import os
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'YURUYURI_10/BDMV/STREAM/00001.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -25)], f"{os.path.splitext(path)[0]}.wav", f"{__file__[:-3]}_cut.wav")
