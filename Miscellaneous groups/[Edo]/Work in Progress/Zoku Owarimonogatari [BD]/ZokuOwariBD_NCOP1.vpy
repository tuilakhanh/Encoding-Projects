import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192


src = lvf.src(r"Zoku_Owarimonogatari\BDMV\STREAM\00009.m2ts")[24:1500]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, width=None, height=720, kernel='bicubic', a1=0, a2=1, mask_detail=False)
scaled = fvf.Depth(scaled, 16)
scaled = nnedi3_rpow2(scaled)
scaled = core.resize.Spline36(scaled, 1920, 1080)
scaled = kgf.join([scaled, U, V])

denoise = lvf.qden(scaled, h=0.8, sigma=4)
aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)

deband = core.f3kdb.Deband(denoise, range=14, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)

mask = kgf.retinex_edgemask(aa)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)


grain = kgf.adaptive_grain(maskedmerge, 0.1, luma_scaling=6)

out = grain
final = fvf.Depth(out, 10)
final.set_output()
