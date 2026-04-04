from libc.stdint cimport int64_t, uint32_t, uint64_t
from vapoursynth4 cimport (
    VSAPI,
    VSAudioFormat,
    VSAudioInfo,
    VSCore,
    VSFrame,
    VSFunction,
    VSLogHandle,
    VSLogHandler,
    VSLogHandlerFree,
    VSMap,
    VSNode,
    VSPlugin,
    VSPluginFunction,
    VSVideoFormat,
    VSVideoInfo,
)


cdef class EnvironmentData:
    cdef bint alive
    cdef Core core
    cdef int coreCreationFlags
    cdef object env_locals
    cdef VSLogHandle* log
    cdef list on_destroy
    cdef dict outputs
    cdef object __weakref__

cdef class EnvironmentPolicy:
    pass
cdef class StandaloneEnvironmentPolicy(EnvironmentPolicy):
    cdef EnvironmentPolicyAPI _api
    cdef EnvironmentData _environment
    cdef int _flags
    cdef object _logger

    cdef object __weakref__

cdef void _set_logger(EnvironmentData env, VSLogHandler handler, VSLogHandlerFree free, void *userData)
cdef void _unset_logger(EnvironmentData env)
cdef void _logCb(int msgType, const char *msg, void *userData) noexcept nogil
cdef void _logFree(void* userData) noexcept nogil

cdef class EnvironmentPolicyAPI:
    # This must be a weak-ref to prevent a cyclic dependency that happens if the API
    # is stored within an EnvironmentPolicy-instance.
    cdef object _known_environments
    cdef object _lock
    cdef object _target_policy

    cdef ensure_policy_matches(self)
cdef EnvironmentPolicy get_policy()
cdef clear_policy(bint delay = *)
cdef EnvironmentData _env_current()

cdef class _FastManager:
    cdef EnvironmentData target
    cdef EnvironmentData previous


cdef class Environment:
    cdef readonly object env
    cdef EnvironmentData get_env(self)

cdef class Local:
    cdef object __weakref__
cdef Environment use_environment(EnvironmentData env)
cdef _get_output_dict(str funcname)

cdef class FuncData: 
    cdef VSCore *core
    cdef EnvironmentData env
    cdef object func
cdef FuncData createFuncData(object func, VSCore *core, EnvironmentData env)

cdef class Func: 
    cdef const VSAPI *funcs
    cdef VSFunction *ref

cdef Func createFuncPython(object func, VSCore *core, const VSAPI *funcs)
cdef Func createFuncRef(VSFunction *ref, const VSAPI *funcs)

cdef class CallbackData: 
    cdef object callback
    cdef EnvironmentData env
    cdef const VSAPI *funcs
    cdef RawNode node

cdef createCallbackData(const VSAPI* funcs, RawNode node, object cb)

cdef class FramePtr: 
    cdef const VSFrame *f
    cdef const VSAPI *funcs

cdef FramePtr createFramePtr(const VSFrame *f, const VSAPI *funcs)
cdef void frameDoneCallback(void *data, const VSFrame *f, int n, VSNode *node, const char *errormsg) noexcept nogil
cdef object intToRangeFilter(int64_t value, str key)
cdef int64_t rangeToIntFilter(object value, str key)
cdef object mapToDict(const VSMap *map, bint flatten)
cdef void dictToMap(dict ndict, VSMap *inm, VSCore *core, const VSAPI *funcs) except *
cdef void typedDictToMap(dict ndict, dict atypes, VSMap *inm, VSCore *core, const VSAPI *funcs, bint filterAllInts) except *

cdef class VideoFormat: 
    cdef readonly object color_family
    cdef readonly object sample_type
    cdef readonly int bits_per_sample
    cdef readonly int bytes_per_sample
    cdef readonly int subsampling_w
    cdef readonly int subsampling_h
    cdef readonly int num_planes
    cdef readonly uint32_t id
    cdef readonly str name

cdef VideoFormat createVideoFormat(const VSVideoFormat *f, const VSAPI *funcs, VSCore *core)

cdef class AudioFormat:
    cdef uint64_t channelLayout
    cdef readonly object sample_type
    cdef readonly int bits_per_sample
    cdef readonly int bytes_per_sample
    cdef readonly int num_channels
    cdef readonly str name

cdef AudioFormat createAudioFormat(const VSAudioFormat *f, const VSAPI *funcs, VSCore *core)

cdef class FrameProps: 
    cdef VSCore *core
    cdef RawFrame frame
    cdef const VSAPI *funcs
    cdef bint readonly

cdef FrameProps createFrameProps(RawFrame f)

cdef class RawFrame:
    cdef const VSFrame *constf
    cdef VSCore *core
    cdef VSFrame *f
    cdef unsigned flags
    cdef const VSAPI *funcs
    cdef object __weakref__

    cdef _ensure_open(self)

cdef class VideoFrame(RawFrame): 
    cdef readonly VideoFormat format
    cdef readonly int height
    cdef readonly int width

cdef VideoFrame createConstVideoFrame(const VSFrame *constf, const VSAPI *funcs, VSCore *core)
cdef VideoFrame createVideoFrame(VSFrame *f, const VSAPI *funcs, VSCore *core)

cdef void* _frame_getdata(VSFrame* frame, int index, unsigned* flags, const VSAPI* lib) noexcept nogil

cdef class _2dview: 
    cdef Py_buffer base
    cdef ssize_t[4] smalltable  # shape, strides

cdef class _video:
    @staticmethod
    cdef _2dview allocinfo(const VSVideoFormat* format)
    @staticmethod
    cdef void fillinfo(Py_buffer* view, VSFrame* frame, int plane, unsigned* flags, const VSAPI* lib) nogil
    @staticmethod
    cdef void filllineinfo(Py_buffer* view, VSFrame* frame, int plane, int line, unsigned* flags, const VSAPI* lib) nogil

cdef class AudioFrame(RawFrame):
    cdef readonly AudioFormat format

cdef AudioFrame createConstAudioFrame(const VSFrame *constf, const VSAPI *funcs, VSCore *core)
cdef AudioFrame createAudioFrame(VSFrame *f, const VSAPI *funcs, VSCore *core)

cdef class _1dview_contig: 
    cdef Py_buffer base
    cdef ssize_t[1] smalltable  # shape


cdef class _audio:
    @staticmethod
    cdef _1dview_contig allocinfo(const VSAudioFormat* format)
    @staticmethod
    cdef void fillinfo(Py_buffer* view, VSFrame* frame, int channel, unsigned* flags, const VSAPI* lib) nogil
cdef _get_handle_future()

cdef class RawNode:
    cdef Core core
    cdef const VSAPI *funcs
    cdef VSNode *node
    cdef object __weakref__

    cdef ensure_valid_frame_number(self, int n)
    cdef bint _inspectable(self)

cdef class VideoNode(RawNode):
    cdef const VSVideoInfo *vi
    cdef readonly VideoFormat format
    cdef readonly object fps
    cdef readonly int64_t fps_den
    cdef readonly int64_t fps_num
    cdef readonly int height
    cdef readonly int num_frames
    cdef readonly int width

    cdef ensure_valid_frame_number(self, int n)
cdef VideoNode createVideoNode(VSNode *node, const VSAPI *funcs, Core core)

cdef class AudioNode(RawNode):
    cdef const VSAudioInfo *ai
    cdef readonly AudioFormat format
    cdef readonly int num_frames
    cdef readonly int64_t num_samples
    cdef readonly int sample_rate

    cdef ensure_valid_frame_number(self, int n)
cdef AudioNode createAudioNode(VSNode *node, const VSAPI *funcs, Core core)

cdef class LogHandle: 
    cdef VSLogHandle *handle
    cdef object handler_func

cdef LogHandle createLogHandle(object handler_func)
cdef void log_handler_wrapper(int msgType, const char *msg, void *userData) noexcept nogil
cdef void log_handler_free(void *userData) noexcept nogil

cdef class CoreTimings: 
    cdef Core core
    cdef object __weakref__

cdef CoreTimings createCoreTimings(Core core)

cdef class Core:
    cdef VSCore *core
    cdef int creationFlags
    cdef const VSAPI *funcs
    cdef readonly CoreTimings timings
    cdef object __weakref__
cdef object createNode(VSNode *node, const VSAPI *funcs, Core core)
cdef object createConstFrame(const VSFrame *f, const VSAPI *funcs, VSCore *core)
cdef Core createCore(EnvironmentData env)
cdef Core createCore2(VSCore *core)
cdef Core _get_core()
cdef Core vsscript_get_core_internal(EnvironmentData env)

cdef class _CoreProxy: 
    pass

cdef class Plugin:
    cdef Core core
    cdef const VSAPI *funcs
    cdef readonly str identifier
    cdef object injected_arg
    cdef readonly str name
    cdef readonly str namespace
    cdef VSPlugin *plugin
    cdef is_video_injectable(self)
    cdef is_audio_injectable(self)
cdef Plugin createPlugin(VSPlugin *plugin, const VSAPI *funcs, Core core)

cdef class Function:
    cdef const VSAPI *funcs
    cdef const VSPluginFunction *func
    cdef readonly str name
    cdef readonly Plugin plugin
    cdef readonly str return_signature
    cdef readonly str signature

    cdef is_video_injectable(self)
    cdef is_audio_injectable(self)
cdef Function createFunction(VSPluginFunction *func, Plugin plugin, const VSAPI *funcs)
cdef void freeFunc(void *pobj) noexcept nogil
cdef void publicFunction(const VSMap *inm, VSMap *outm, void *userData, VSCore *core, const VSAPI *vsapi) noexcept nogil

cdef const VSAPI *getVSAPIInternal() except NULL nogil