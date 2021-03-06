import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import mvsfunc as mvf
import debandshit as ds
import awsmfunc as awsm
from toolz import functoolz
from nnedi3_resample import nnedi3_resample
from descale import get_filter
from vsTAAmbk import TAAmbk
from vsutil import *
core = vs.core
core.max_cache_size = 128000
core.num_threads = 36


@functoolz.curry
def _unsharp(clip: vs.VideoNode, strength: float = 1.0) -> vs.VideoNode:
    planes = split(clip)
    l_mask = fvf.Depth(kgf.retinex_edgemask(fvf.Depth(planes[0], 16)), 32)
    blurred_clip = core.std.Convolution(planes[0], matrix=[1, 2, 1, 2, 4, 2, 1, 2, 1])
    unsharp = core.std.Expr(clips=[planes[0], blurred_clip], expr=['x y - ' + str(strength) + ' * x +'])
    planes[0] = core.std.MaskedMerge(planes[0], unsharp, l_mask)
    return join(planes).rgsf.Repair(clip, 13)


@functoolz.curry
def _fix_lineart(clip: vs.VideoNode) -> vs.VideoNode:
    if get_depth(clip) != 16:
        clip, clip_c = fvf.Depth(clip, 16), clip
    dehalo = haf.FineDehalo(clip, rx=2.8, thmi=91, thma=128, darkstr=0.3, brightstr=1, contra=1)
    dering = haf.EdgeCleaner(dehalo, strength=1, rmode=13, smode=1, hot=True)
    return fvf.Depth(dering, get_depth(clip_c))


@functoolz.curry
def _denoise(clip: vs.VideoNode) -> vs.VideoNode:
    denY = core.knlm.KNLMeansCL(clip, d=2, a=3, h=0.6)
    return fvf.Depth(core.knlm.KNLMeansCL(clip, d=2, a=3, h=1, channels="UV"), 16)


@functoolz.curry
def _dark_aa(clip: vs.VideoNode) -> vs.VideoNode:
    if get_depth(clip) != 16:
        clip, clip_c = fvf.Depth(clip, 16), clip
    darken = haf.FastLineDarkenMOD(clip, strength=24, protection=6, luma_cap=235)
    return fvf.Depth(TAAmbk(darken, aatype='Eedi3', repair=12, opencl=True), get_depth(clip_c))

@functoolz.curry
def _denoiseNgrain(clip: vs.VideoNode, src: vs.VideoNode) -> vs.VideoNode:
    m_denoised = core.knlm.KNLMeansCL(clip, h=1)
    maska = fvf.Depth(ds.rangemask(get_y(fvf.Depth(m_denoised, 16)), 3, 2), 32).std.Binarize(0.2)
    maskb = get_y(clip).std.Prewitt().std.Binarize(0.045)
    mask = core.std.Expr([maska, maskb], 'x y max').rgsf.RemoveGrain(22).rgsf.RemoveGrain(11)

    deband = core.placebo.Deband(clip, planes=1, threshold=5, radius=20, iterations=2)
    deband = core.placebo.Deband(deband, planes=2|4, threshold=3, grain=0)
    deband = core.std.MaskedMerge(deband, clip, mask)

    return kgf.adaptive_grain(deband, 0.2, luma_scaling=6)


src = lvf.src(r"BDMV/[BDMV][191127] Fate／kaleid liner Prisma☆Illya Prisma☆Phantasm/PRISMAPHANTASM_SP/BDMV/STREAM/00005.m2ts")[24:-24]
limit = core.std.Limiter(src, 16, [235,240])
src = fvf.Depth(limit, 32)


filter_chain = functoolz.compose(_denoise, _unsharp(strength=0.25), _fix_lineart, _dark_aa, _denoiseNgrain(src=src))
main_filter = filter_chain(src)


out = main_filter
final = fvf.Depth(out, 10)
final.set_output()
