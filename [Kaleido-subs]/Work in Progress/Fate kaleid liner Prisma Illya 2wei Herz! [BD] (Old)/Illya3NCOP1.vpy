import vapoursynth as vs
import mvsfunc as mvf
import vsTAAmbk as taa	
import kagefunc as kgf
core = vs.core

opstart = 0
denoiseframesOPa = f'[{opstart+0} {opstart+499}] [{opstart+859} {opstart+918}] [{opstart+1804} {opstart+1868}] [{opstart+1974} {opstart+2029}]'
denoiseframesOPb = f'[{opstart+500} {opstart+666}]'
debandframesOPa = f'[{opstart+0} {opstart+142}] [{opstart+824} {opstart+858}] [{opstart+919} {opstart+960}] [{opstart+2029} {opstart+2159}]'
debandframesOPb = f'[{opstart+1334} {opstart+1801}]'
dynamicgrainframesOP = f'[{opstart+824} {opstart+858}] [{opstart+1334} {opstart+1739}]'
replaceframesOP = f'[{opstart+0} {opstart+499}] [{opstart+859} {opstart+918}] [{opstart+1146} {opstart+1333}] [{opstart+1804} {opstart+1868}] [{opstart+1974} {opstart+2029}]'

src = core.lsmas.LWLibavSource(r"F:\Convert\Fate／kaleid liner プリズマ☆イリヤ ツヴァイ ヘルツ!Vol.1~Vol.5\[BDMV][アニメ][150925]Fate／kaleid liner プリズマ☆イリヤ ツヴァイ ヘルツ! Vol.1\BDMV\STREAM\00013.m2ts")
src = core.std.Trim(src, 24, 2183)

scaled = kgf.inverse_scale(
    src, width=None, height=720, kernel='bicubic', a1=1/3, a2=1/3,
    kerneluv='blackman', mask_detail=False, masking_areas=None, 
    mask_threshold=0.05, show_mask=False, denoise=False, use_gpu=True)
scaled = core.fmtc.bitdepth(scaled, bits=16)

srcY, srcU, srcV = kgf.split(scaled)
denoiseY1 = srcY.knlm.KNLMeansCL(3, 2, h=0.2)
denoiseY1 = mvf.BM3D(srcY, sigma=3, psample=1, radius1=1, ref=denoiseY1)
denoiseY2 = srcY.knlm.KNLMeansCL(3, 2, h=1.4)
denoiseY2 = mvf.BM3D(srcY, sigma=3, psample=1, radius1=1, ref=denoiseY2)
denoiseY3 = srcY.knlm.KNLMeansCL(3, 2, h=1.4)
denoiseY3 = mvf.BM3D(srcY, sigma=8, psample=1, radius1=1, ref=srcY)
denoiseY = core.remap.Rfs(denoiseY1, denoiseY2, mappings=denoiseframesOPa)
#denoiseY = core.remap.Rfs(denoiseY, denoiseY3, mappings=denoiseframesOPb)
denoised = kgf.join([denoiseY, srcU, srcV])

aa = taa.TAAmbk(denoised, aatype='Eedi3', opencl=True)

deband1 = core.f3kdb.Deband(aa, range=20, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband2 = core.f3kdb.Deband(aa, range=21, y=56, cb=48, cr=48, grainy=36, grainc=0, output_depth=16)
deband3 = core.f3kdb.Deband(aa, range=14, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband = core.remap.Rfs(deband1, deband2, mappings=debandframesOPa)
deband = core.remap.Rfs(deband, deband3, mappings=debandframesOPb)

mask = kgf.retinex_edgemask(aa, sigma=1)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

grain1 = kgf.adaptive_grain(maskedmerge, 0.3, mask_bits=10, luma_scaling=16, static=True)
grain2 = kgf.adaptive_grain(maskedmerge, 0.8, mask_bits=10, luma_scaling=16, static=False)
grain = core.remap.Rfs(grain1, grain2, mappings=dynamicgrainframesOP)

out = core.remap.Rfs(grain, aa, mappings=replaceframesOP)

final = core.fmtc.bitdepth(out, bits=10, dmode=3)
final.set_output()