#!/usr/bin/env python3
import os
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'01/227 - 01v2 (Funimation 1080p).mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(289, 0)], f"{os.path.splitext(path)[0]}_Track02.aac", f"{__file__[:-3]}_cut.aac")
