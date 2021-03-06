#!/usr/bin/env python3
import os
from acsuite import eztrim
import lvsfunc as lvf


path = r'BDMV/[BDMV][190302][マナリアフレンズ I]/BD/BDMV/STREAM/00012.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (2011, 2994), f"{os.path.splitext(path)[0]}.wav", f"{__file__[3:-3]}_cut.wav")
