#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import os

preview = 16662
endcard = 16782
part_b = 16902
epend = 20904


core = vs.core
ts_in = r"06/[DragsterPS] Manariafurenzu Ekusutorapaato Zuke S01E06 [1080p] [Japanese Audio] [6C77A337].mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(0,preview-1),(endcard,endcard+48),(part_b,epend),(preview,part_b)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('06/06_cut.mka', audio_source='06/track1_jpn.mka')
    
os.remove("tmp-001.mka")
os.remove("tmp-002.mka")
os.remove("tmp-003.mka")
os.remove("tmp-004.mka")

# NOTE FOR MANARIA:
#		Make sure to use the E-AC3 audio from danimestore Amazon, NOT the AAC from Crunchyroll
#		It's more work and not worth the effort!