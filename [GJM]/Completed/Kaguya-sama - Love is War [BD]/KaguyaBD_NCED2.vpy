import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import mvsfunc as mvf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core


src = lvf.src(r"BDMV/かぐや様は告らせたい Vol.2/BD/BDMV/STREAM/00009.m2ts")
src = src[:2349]

shift = haf.FixChromaBleedingMod(src, cx=0.5, cy=0, thr=100, strength=1, blur=True)
Y, U, V = kgf.split(shift)

scaled = kgf.inverse_scale(Y, height=874, kernel='bicubic', b=0, c=1/2)
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P8)
scaled = kgf.join([scaled, U, V])

scaled = core.std.CropRel(scaled, 0, 0, 132, 134)#.resize.Spline36(1920, 816)
scaled = core.edgefixer.ContinuityFixer(scaled, [4,2,2], [4,2,2], [4,2,2], [4,2,2])
scaled = core.std.AddBorders(scaled, 0, 0, 132, 134)
scaled = fvf.Depth(scaled, 16)

denoise = mvf.BM3D(scaled, sigma=[3,0.5])
deband = core.f3kdb.Deband(denoise, range=18, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=10)


out = grain
final = fvf.Depth(out, 10)
final.set_output()