project('VapourSynth', 'c', 'cpp', 'cython',
    default_options: ['buildtype=release', 'b_lto=true', 'b_ndebug=if-release', 'c_std=c11', 'cpp_std=c++17'],
    license: 'LGPL-2.1-or-later',
    license_files: 'COPYING.LESSER',
    meson_version: '>=1.3.0',
    version: '77',
)

enable_guard_pattern = get_option('enable_guard_pattern')
enable_x86_asm = get_option('enable_x86_asm')

cxx = meson.get_compiler('cpp')

if cxx.get_argument_syntax() == 'gcc'
    avx2_args = '-march=x86-64-v3'
elif cxx.get_id() == 'clang-cl'
    avx2_args = '/clang:-march=x86-64-v3'
else
    avx2_args = '/arch:AVX2'
endif

host_system = host_machine.system()
is_win = host_system in ['cygwin', 'windows']

if is_win
    dl_dep = dependency('', required: false)
    libp2p_dep = dependency('libp2p')
else
    dl_dep = dependency('dl')
endif

if not host_machine.cpu_family().startswith('x86')
    enable_x86_asm = false
endif

incdir = include_directories('include')

py = import('python').find_installation(pure: false)
py_dep = py.dependency(version: is_win ? '>=3.14' : '>=3.12')  # Py_NO_LINK_LIB was introduced in 3.14

install_dir = py.get_install_dir() / 'vapoursynth'

vs_current_release = run_command(
    py,
    '-c',
    'print(open("VAPOURSYNTH_VERSION").read())',
    check: true,
).stdout().strip().split()[2].split('-')[0]

if get_option('buildtype') == 'release'
    if cxx.get_id() == 'clang-cl'
        add_project_arguments('/clang:-flto', '/clang:-O3', language: ['c', 'cpp'])
    endif
endif

add_project_arguments(
    cxx.get_supported_arguments(
        '-D_CRT_SECURE_NO_WARNINGS',
        '-DNOMINMAX',
        '-DVS_CURRENT_RELEASE=@0@'.format(vs_current_release),
        '-DVS_GRAPH_API',
        '-DVS_USE_LATEST_API',
        '-DVSSCRIPT_USE_LATEST_API',
        '-Wno-ignored-attributes',
    ),
    language: ['c', 'cpp'],
)

if is_win
    add_project_arguments('-DVS_TARGET_OS_WINDOWS', '-D_UNICODE', '-DUNICODE', language: ['c', 'cpp'])
    if cxx.get_id() == 'msvc'
        add_project_arguments('/wd4551', language: ['c', 'cpp'])
    endif
elif host_system == 'darwin'
    add_project_arguments('-DVS_TARGET_OS_DARWIN', language: ['c', 'cpp'])
elif host_system in ['dragonfly', 'freebsd', 'gnu', 'linux', 'netbsd', 'openbsd']
    add_project_arguments('-DVS_TARGET_OS_LINUX', language: ['c', 'cpp'])
else
    warning('Unknown host OS')
endif

if enable_guard_pattern
    add_project_arguments('-DVS_FRAME_GUARD', language: ['c', 'cpp'])
endif

if host_system not in ['cygwin', 'windows']
    code = '''
#define _GNU_SOURCE
#include <sched.h>

int main() {
    cpu_set_t affinity;
    sched_getaffinity(0, sizeof(cpu_set_t), &affinity);
    int count = CPU_COUNT(&affinity);
}
'''

    if cxx.links(code, name: 'sched_getaffinity')
        add_project_arguments('-DHAVE_SCHED_GETAFFINITY', language: ['c', 'cpp'])
    endif

    code = '''
#include <sys/param.h>
#include <sys/_cpuset.h>
#include <sys/cpuset.h>

int main() {
    cpuset_t affinity;
    cpuset_getaffinity(CPU_LEVEL_WHICH, CPU_WHICH_PID, -1, sizeof(cpuset_t), &affinity);
    int count = CPU_COUNT(&affinity);
}
'''

    if cxx.links(code, name: 'cpuset_getaffinity')
        add_project_arguments('-DHAVE_CPUSET_GETAFFINITY', language: ['c', 'cpp'])
    endif
endif

deps = [
    dl_dep,
    dependency('threads'),
    dependency('zimg', version: '>=3.0.5'),
]

libs = []

soversion = is_win ? '' : run_command(
    'grep',
    '-m',
    '1',
    'VAPOURSYNTH_API_MAJOR',
    'include/VapourSynth4.h',
    check: true,
).stdout().strip().split()[2]

if enable_x86_asm
    add_project_arguments('-DVS_TARGET_CPU_X86', language: ['c', 'cpp'])

    libs += static_library('core_sse2',
        files(
            'src/core/expr/jitcompiler_x86.cpp',
            'src/core/kernel/x86/average_sse2.c',
            'src/core/kernel/x86/convolution_sse2.cpp',
            'src/core/kernel/x86/generic_sse2.cpp',
            'src/core/kernel/x86/merge_sse2.c',
            'src/core/kernel/x86/planestats_sse2.c',
            'src/core/kernel/x86/transpose_sse2.c',
        ),
        gnu_symbol_visibility: 'hidden',
        include_directories: incdir,
    )

    libs += static_library('core_avx2',
        files(
            'src/core/kernel/x86/convolution_avx2.cpp',
            'src/core/kernel/x86/generic_avx2.cpp',
            'src/core/kernel/x86/merge_avx2.c',
            'src/core/kernel/x86/planestats_avx2.c',
        ),
        c_args: avx2_args,
        cpp_args: avx2_args,
        gnu_symbol_visibility: 'hidden',
        include_directories: incdir,
    )
endif

libvapoursynth = library('libvapoursynth',
    files(
        'src/core/expr/expr.cpp',
        'src/core/expr/jitcompiler.cpp',
        'src/core/kernel/average.cpp',
        'src/core/kernel/cpulevel.cpp',
        'src/core/kernel/generic.cpp',
        'src/core/kernel/merge.c',
        'src/core/kernel/planestats.c',
        'src/core/kernel/transpose.c',
        'src/core/audiofilters.cpp',
        'src/core/averageframesfilter.cpp',
        'src/core/boxblurfilter.cpp',
        'src/core/cpufeatures.cpp',
        'src/core/exprfilter.cpp',
        'src/core/genericfilters.cpp',
        'src/core/lutfilters.cpp',
        'src/core/memoryuse.cpp',
        'src/core/mergefilters.cpp',
        'src/core/reorderfilters.cpp',
        'src/core/simplefilters.cpp',
        'src/core/textfilter.cpp',
        'src/core/vsapi.cpp',
        'src/core/vscore.cpp',
        'src/core/vslog.cpp',
        'src/core/vsresize.cpp',
        'src/core/vsthreadpool.cpp',
    ),
    c_args: '-DVS_CORE_EXPORTS',
    cpp_args: '-DVS_CORE_EXPORTS',
    dependencies: deps,
    gnu_symbol_visibility: 'hidden',
    include_directories: incdir,
    install: true,
    install_dir: install_dir,
    link_with: libs,
    name_prefix: '',
    soversion: soversion,
)

vapoursynth_dep = declare_dependency(
    include_directories: incdir,
    link_with: libvapoursynth,
)

        py_ext_kwargs = {
            'cython_args': ['-I' + meson.project_source_root() / 'src/pybindings'],
            'dependencies': [py_dep, vapoursynth_dep],
            'include_directories': [include_directories('src/pybindings'), include_directories('src/vsutils')],
            'install': true,
            'install_rpath': '$ORIGIN',
            'limited_api': '3.12',
            'override_options': 'cython_language=cpp',
            'subdir': 'vapoursynth',
        }

        py.extension_module('_main',
            files(
                'src/common/wave.cpp',
                'src/vsutils/printgraph.cpp',
                'src/vsutils/vsjson.cpp',
                'src/pybindings/_main.pyx'
            ),
            kwargs: py_ext_kwargs,
        )

        py.extension_module('_constants',
            files('src/pybindings/_constants.pyx'),
            kwargs: py_ext_kwargs,
        )

py.install_sources(
    files(
        'src/pybindings/__init__.py',
        'src/pybindings/__main__.py',
        'src/pybindings/_cli.py',
        'src/pybindings/_shell.py',
        'src/pybindings/_signatures.py',
                'src/pybindings/_utils.py',
        'src/pybindings/_constants.pyi',
                'src/pybindings/_main.pyi',
    ),
    subdir: 'vapoursynth',
)

        py.install_sources(
            files(
                'src/pybindings/vspipe/__init__.py',
                'src/pybindings/vspipe/_cli.py',
                'src/pybindings/vspipe/_utils.py',
                'src/pybindings/vspipe/_vsenv.py',
            ),
            subdir: 'vapoursynth/vspipe',
        )

libvsscript = library('vsscript',
    files('src/vsscript/vsscript.cpp'),
    cpp_args: ['-DPy_NO_LINK_LIB', '-DVS_CORE_EXPORTS'],
    dependencies: [dl_dep, py_dep],
    gnu_symbol_visibility: 'hidden',
    include_directories: incdir,
    install: true,
    install_dir: install_dir,
)

vsscript_dep = declare_dependency(
    include_directories: incdir,
    link_with: libvsscript,
)


if cxx.get_argument_syntax() == 'msvc'
    vsvfw = library('vsvfw',
        files(
            'src/common/fourcc.cpp',
            'src/common/wave.cpp',
            'src/vfw/vsvfw.cpp',
        ),
        dependencies: [libp2p_dep, vsscript_dep],
        gnu_symbol_visibility: 'hidden',
        install: true,
        install_dir: install_dir,
        vs_module_defs: 'src/vfw/vsvfw.def',
    )

    avscompat = shared_module('avscompat',
        files(
            'src/avisynth/avisynth_compat.cpp',
            'src/avisynth/interface.cpp',
            'src/core/cpufeatures.cpp',
        ),
        cpp_args: '-DBUILDING_AVSCORE',
        dependencies: libp2p_dep,
        gnu_symbol_visibility: 'hidden',
        include_directories: [incdir, include_directories('src/avisynth')],
        install: true,
        install_dir: install_dir / 'plugins',
    )
endif

install_subdir(
    'include',
    exclude_directories: 'cython',
    exclude_files: ['VapourSynth.h', 'VSHelper.h'],
    install_dir: install_dir,
)

pc_data = configuration_data()
pc_data.set('version', meson.project_version())
configure_file(
    configuration: pc_data,
    input: 'vapoursynth.pc.in',
    install: true,
    install_dir: install_dir / 'pkgconfig',
    output: 'vapoursynth.pc',
)
