#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/JOSHIRAKU/130522_JOSHIRAKU_VOL6/BDMV/STREAM/00000.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(34815, 69581)], path[:-4]+"wav", "JoshirakuBD_12_cut.wav")
