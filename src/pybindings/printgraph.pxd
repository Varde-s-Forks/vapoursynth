from libc.stdint cimport int64_t
from libcpp.string cimport string
from vapoursynth4 cimport VSAPI, VSNode

cdef extern from "printgraph.h" nogil:
    cdef enum class NodePrintMode:
        Simple
        Full
        FullWithTimes

    string printNodeGraph(NodePrintMode mode, VSNode *node, double processingTime, const VSAPI *vsapi)
    string printNodeTimes(VSNode *node, double processingTime, int64_t freedTime, const VSAPI *vsapi)
