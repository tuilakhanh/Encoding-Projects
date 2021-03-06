from functools import partial

import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
import mvsfunc as mvf
from descale import Debicubic
from nnedi3_resample import nnedi3_resample
from toolz import functoolz
from vsutil import get_w, get_y, iterate, join, split

import lvsfunc as lvf
import vapoursynth as vs

core = vs.core


@functoolz.curry
def denoise(clip: vs.VideoNode) -> vs.VideoNode:
    detail_mask = _generate_detail_mask(clip)
    denoise = mvf.BM3D(clip, sigma=[1.2,0], profile1='lc')
    denoise = core.std.MaskedMerge(denoise, clip, detail_mask)
    return mvf.BM3D(clip, sigma=[0,1.6], profile1='lc')


@functoolz.curry
def fix_lineart(clip: vs.VideoNode) -> vs.VideoNode:
    dehalo = lvf.util.quick_resample(clip, partial(haf.FineDehalo, rx=2.4, darkstr=0, brightstr=1, contra=1))
    return lvf.util.quick_resample(dehalo, partial(haf.EdgeCleaner, strength=4, rmode=13, smode=1, hot=True))


@functoolz.curry
def merge_credits(clip: vs.VideoNode, og_clip: vs.VideoNode,
                  h: int, b: float, c: float) -> vs.VideoNode:
    credit_mask = _create_credit_mask(og_clip, h, b, c, brz=0.1)
    return core.std.MaskedMerge(clip, og_clip, credit_mask)


@functoolz.curry
def deband(clip: vs.VideoNode, og_clip: vs.VideoNode) -> vs.VideoNode:
    detail_mask = _generate_detail_mask(og_clip)
    deband = core.placebo.Deband(clip, planes=1, iterations=1, threshold=2, radius=12, grain=8)
    deband = core.std.MaskedMerge(deband, og_clip, detail_mask)
    deband = core.placebo.Deband(deband, planes=2|4, iterations=2, threshold=3, radius=20, grain=0)
    return kgf.adaptive_grain(deband, 0.35, luma_scaling=4)


def dehardsub(clip_a: vs.VideoNode, clip_b: vs.VideoNode) -> vs.VideoNode:
    hardsubmask = kgf.hardsubmask(clip_a, clip_b)
    clip = core.std.MaskedMerge(clip_a, clip_b, hardsubmask)

    hardsubmask_fade = lvf.util.quick_resample(clip_a, partial(kgf.hardsubmask_fades, ref=clip_b, highpass=1200))
    clip_fade = core.std.MaskedMerge(clip_a, clip_b, hardsubmask_fade)
    clip = lvf.rfs(clip, clip_fade, ranges=op_signs + hs_signs)
    if replace_scenes:
        clip = lvf.rfs(clip, clip_b, ranges=replace_scenes)
    return clip


def rescale_blur(clip: vs.VideoNode, h: int, b: float, c: float) -> vs.VideoNode:
    planes = split(clip)
    descaled = Debicubic(planes[0], get_w(h), h, b=b, c=c)

    pre_den = core.knlm.KNLMeansCL(descaled, d=2, a=3, h=1.2, device_type='gpu')
    l_mask = core.std.Prewitt(pre_den, scale=5)
    l_mask = iterate(l_mask, core.std.Deflate, 6).std.Binarize(0.08)

    blur = lvf.util.quick_resample(descaled, partial(core.bilateral.Bilateral, sigmaS=4.5, sigmaR=0.01))
    blur = core.std.MaskedMerge(descaled, blur, l_mask)
    blur = lvf.rfs(descaled, blur, ranges=op_range)

    interp = lvf.util.quick_resample(blur, partial(haf.QTGMC, InputType=1, TR2=3))
    interp = lvf.rfs(blur, interp, ranges=op_interp)

    planes[0] = nnedi3_resample(interp, planes[0].width, planes[0].height, kernel='gauss',
                                invks=True, invkstaps=2, taps=1, a1=32, nns=4, qual=2, pscrn=4)
    return join(planes)


def _create_credit_mask(clip: vs.VideoNode, h: int, b: float, c: float, brz: float = 0.05) -> vs.VideoNode:
    clip_y = get_y(clip)
    descaled = Debicubic(clip_y, get_w(h), h, b=b, c=c)
    upscaled =  core.resize.Bicubic(descaled, clip_y.width, clip_y.height, filter_param_a=b, filter_param_b=c)
    credit_mask = core.std.Expr([clip_y, upscaled], 'x y - abs').std.Binarize(brz)
    credit_mask = iterate(credit_mask, core.std.Maximum, 4)
    return iterate(credit_mask, core.std.Inflate, 2)


def _generate_detail_mask(clip: vs.VideoNode) -> vs.VideoNode:
    return lvf.denoise.detail_mask(clip, pre_denoise=3.6, brz_a=0.025, brz_b=0.005)


opstart          = 0

op_signs         = [(opstart+397,opstart+508)] if opstart is not None else []
hs_signs         = [(2380, 2697), (6726, 6808), (7578, 7609), (7776, 7863),
                    (8167, 8195), (11053, 11061), (11123, 11133), (11150, 11194),
                    (11209, 11269), (12970, 13023), (13351, 13412), (13966, 14001),
                    (21767, 21886), (21942, 22105), (22181, 22405), (25425, 25463),
                    (26602, 26672), (27170, 27175), (27180, 27181), (27186, 27187),
                    (27192, 27193), (27198, 27199), (27204, 27205), (27210, 27211),
                    (27216, 27217), (27222, 27223), (27228, 27229), (27234, 27235),
                    (27240, 27241), (27246, 27247), (27252, 27253), (27258, 27259),
                    (27264, 27265), ]

replace_scenes   = []
op_range         = [(opstart,opstart+2157)] if opstart is not None else []
op_interp        = [(opstart+594,opstart+628)] if opstart is not None else []


src_wk = lvf.misc.source(r"06/Kaguya_S2_06_EN_HD.mp4")
src_fu = lvf.misc.source(r"06/[HorribleSubs] Kaguya-sama wa Kokurasetai S2 - 06 [1080p].mkv")[289:]
src_wk = src_wk[:11734] + src_wk[11733]*13 + src_wk[11734:]
scomp = lvf.comparison.stack_compare(src_wk, src_fu, make_diff=True)

src = dehardsub(src_wk, src_fu)
scomp2 = lvf.comparison.stack_compare(src, src_fu, make_diff=True)


#diff = lvf.comparison.tvbd_diff(src, src_fu)
shift = haf.FixChromaBleedingMod(src, cx=-.65, cy=-.25, thr=100, strength=1, blur=True)
shift = fvf.Depth(shift, 32)


h = 874
b, c =  0, 1/2
scaled = rescale_blur(shift, h=h, b=b, c=c)


filter_chain = functoolz.compose(
    denoise,
    fix_lineart,
    merge_credits(og_clip = shift, h=h, b=b, c=c),
    deband(og_clip = scaled)
)
main_filter = filter_chain(shift)


out = main_filter
final = fvf.Depth(out, 10)
final.set_output()
