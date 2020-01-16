import ocsuite as ocs
import lvsfunc as lvf
oc = ocs.OC()


path = r'BDMV/[BDMV][191204][Lord El-Melloi II-sei no Jikenbo][Vol.04]/BDROM/BDMV/STREAM/00000.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    oc.eztrim(src, [(24, -24)], path[:-4]+"wav", "CaseFilesBD_07_cut.wav")
