from libcpp.string cimport string
from vapoursynth4 cimport VSMap, VSAPI

cdef extern from "vsjson.h" nogil:
    string convertVSMapToJSON(const VSMap *map, const VSAPI *vsapi)
