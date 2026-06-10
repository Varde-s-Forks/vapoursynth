#
# Copyright (c) 2012-2025 Fredrik Mellbin
#
# This file is part of VapourSynth.
#
# VapourSynth is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# VapourSynth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with VapourSynth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

from vsconstants4 cimport *
from vapoursynth4 cimport *

from typing import NamedTuple
from enum import IntEnum, IntFlag


class VapourSynthVersion(NamedTuple):
    release_major: int
    release_minor: int

    def __str__(self):
        if self.release_minor:
            return f'R{self.release_major}.{self.release_minor}'
        return f'R{self.release_major}'

class VapourSynthAPIVersion(NamedTuple):
    api_major: int
    api_minor: int

    def __str__(self):
        return f'R{self.api_major}.{self.api_minor}'


__version__ = VapourSynthVersion(VS_CURRENT_RELEASE, 0)
__api_version__ = VapourSynthAPIVersion(VAPOURSYNTH_API_MAJOR, VAPOURSYNTH_API_MINOR)


class MediaType(IntEnum):
    VIDEO = mtVideo
    AUDIO = mtAudio


class ColorFamily(IntEnum):
    UNDEFINED = cfUndefined
    GRAY = cfGray
    RGB = cfRGB
    YUV = cfYUV


class SampleType(IntEnum):
    INTEGER = stInteger
    FLOAT = stFloat


class PresetVideoFormat(IntEnum):
    NONE = pfNone

    GRAY8 = pfGray8
    GRAY9 = pfGray9
    GRAY10 = pfGray10
    GRAY12 = pfGray12
    GRAY14 = pfGray14
    GRAY16 = pfGray16
    GRAY32 = pfGray32

    GRAYH = pfGrayH
    GRAYS = pfGrayS

    YUV410P8 = pfYUV410P8
    YUV411P8 = pfYUV411P8
    YUV440P8 = pfYUV440P8

    YUV420P8 = pfYUV420P8
    YUV422P8 = pfYUV422P8
    YUV444P8 = pfYUV444P8

    YUV420P9 = pfYUV420P9
    YUV422P9 = pfYUV422P9
    YUV444P9 = pfYUV444P9

    YUV420P10 = pfYUV420P10
    YUV422P10 = pfYUV422P10
    YUV444P10 = pfYUV444P10

    YUV420P12 = pfYUV420P12
    YUV422P12 = pfYUV422P12
    YUV444P12 = pfYUV444P12

    YUV420P14 = pfYUV420P14
    YUV422P14 = pfYUV422P14
    YUV444P14 = pfYUV444P14

    YUV420P16 = pfYUV420P16
    YUV422P16 = pfYUV422P16
    YUV444P16 = pfYUV444P16

    YUV420PH = pfYUV420PH
    YUV420PS = pfYUV420PS

    YUV422PH = pfYUV422PH
    YUV422PS = pfYUV422PS

    YUV444PH = pfYUV444PH
    YUV444PS = pfYUV444PS

    RGB24 = pfRGB24
    RGB27 = pfRGB27
    RGB30 = pfRGB30
    RGB36 = pfRGB36
    RGB42 = pfRGB42
    RGB48 = pfRGB48

    RGBH = pfRGBH
    RGBS = pfRGBS


class FilterMode(IntEnum):
    PARALLEL = fmParallel
    PARALLEL_REQUESTS = fmParallelRequests
    UNORDERED = fmUnordered
    FRAME_STATE = fmFrameState


class AudioChannels(IntEnum):
    FRONT_LEFT = acFrontLeft
    FRONT_RIGHT = acFrontRight
    FRONT_CENTER = acFrontCenter
    LOW_FREQUENCY = acLowFrequency
    BACK_LEFT = acBackLeft
    BACK_RIGHT = acBackRight
    FRONT_LEFT_OF_CENTER = acFrontLeftOFCenter
    FRONT_RIGHT_OF_CENTER = acFrontRightOFCenter
    BACK_CENTER = acBackCenter
    SIDE_LEFT = acSideLeft
    SIDE_RIGHT = acSideRight
    TOP_CENTER = acTopCenter
    TOP_FRONT_LEFT = acTopFrontLeft
    TOP_FRONT_CENTER = acTopFrontCenter
    TOP_FRONT_RIGHT = acTopFrontRight
    TOP_BACK_LEFT = acTopBackLeft
    TOP_BACK_CENTER = acTopBackCenter
    TOP_BACK_RIGHT = acTopBackRight
    STEREO_LEFT = acStereoLeft
    STEREO_RIGHT = acStereoRight
    WIDE_LEFT = acWideLeft
    WIDE_RIGHT = acWideRight
    SURROUND_DIRECT_LEFT = acSurroundDirectLeft
    SURROUND_DIRECT_RIGHT = acSurroundDirectRight
    LOW_FREQUENCY2 = acLowFrequency2


class MessageType(IntFlag):
    MESSAGE_TYPE_DEBUG = mtDebug
    MESSAGE_TYPE_INFORMATION = mtInformation
    MESSAGE_TYPE_WARNING = mtWarning
    MESSAGE_TYPE_CRITICAL = mtCritical
    MESSAGE_TYPE_FATAL = mtFatal


class CoreCreationFlags(IntFlag):
    ENABLE_GRAPH_INSPECTION = ccfEnableGraphInspection
    DISABLE_AUTO_LOADING = ccfDisableAutoLoading
    DISABLE_LIBRARY_UNLOADING = ccfDisableLibraryUnloading
    ENABLE_FRAME_REF_DEBUG = ccfEnableFrameRefDebug


class Range(IntEnum):
    RANGE_FULL = VSC_RANGE_FULL
    RANGE_LIMITED = VSC_RANGE_LIMITED


class ChromaLocation(IntEnum):
    CHROMA_LEFT = VSC_CHROMA_LEFT
    CHROMA_CENTER = VSC_CHROMA_CENTER
    CHROMA_TOP_LEFT = VSC_CHROMA_TOP_LEFT
    CHROMA_TOP = VSC_CHROMA_TOP
    CHROMA_BOTTOM_LEFT = VSC_CHROMA_BOTTOM_LEFT
    CHROMA_BOTTOM = VSC_CHROMA_BOTTOM


class FieldBased(IntEnum):
    FIELD_PROGRESSIVE = VSC_FIELD_PROGRESSIVE
    FIELD_TOP = VSC_FIELD_TOP
    FIELD_BOTTOM = VSC_FIELD_BOTTOM


class MatrixCoefficients(IntEnum):
    MATRIX_RGB = VSC_MATRIX_RGB
    MATRIX_BT709 = VSC_MATRIX_BT709
    MATRIX_UNSPECIFIED = VSC_MATRIX_UNSPECIFIED
    MATRIX_FCC = VSC_MATRIX_FCC
    MATRIX_BT470_BG = VSC_MATRIX_BT470_BG
    MATRIX_ST170_M = VSC_MATRIX_ST170_M
    MATRIX_ST240_M = VSC_MATRIX_ST240_M
    MATRIX_YCGCO = VSC_MATRIX_YCGCO
    MATRIX_BT2020_NCL = VSC_MATRIX_BT2020_NCL
    MATRIX_BT2020_CL = VSC_MATRIX_BT2020_CL
    MATRIX_CHROMATICITY_DERIVED_NCL = VSC_MATRIX_CHROMATICITY_DERIVED_NCL
    MATRIX_CHROMATICITY_DERIVED_CL = VSC_MATRIX_CHROMATICITY_DERIVED_CL
    MATRIX_ICTCP = VSC_MATRIX_ICTCP


class TransferCharacteristics(IntEnum):
    TRANSFER_BT709 = VSC_TRANSFER_BT709
    TRANSFER_UNSPECIFIED = VSC_TRANSFER_UNSPECIFIED
    TRANSFER_BT470_M = VSC_TRANSFER_BT470_M
    TRANSFER_BT470_BG = VSC_TRANSFER_BT470_BG
    TRANSFER_BT601 = VSC_TRANSFER_BT601
    TRANSFER_ST240_M = VSC_TRANSFER_ST240_M
    TRANSFER_LINEAR = VSC_TRANSFER_LINEAR
    TRANSFER_LOG_100 = VSC_TRANSFER_LOG_100
    TRANSFER_LOG_316 = VSC_TRANSFER_LOG_316
    TRANSFER_IEC_61966_2_4 = VSC_TRANSFER_IEC_61966_2_4
    TRANSFER_IEC_61966_2_1 = VSC_TRANSFER_IEC_61966_2_1
    TRANSFER_BT2020_10 = VSC_TRANSFER_BT2020_10
    TRANSFER_BT2020_12 = VSC_TRANSFER_BT2020_12
    TRANSFER_ST2084 = VSC_TRANSFER_ST2084
    TRANSFER_ST428 = VSC_TRANSFER_ST428
    TRANSFER_ARIB_B67 = VSC_TRANSFER_ARIB_B67


class ColorPrimaries(IntEnum):
    PRIMARIES_BT709 = VSC_PRIMARIES_BT709
    PRIMARIES_UNSPECIFIED = VSC_PRIMARIES_UNSPECIFIED
    PRIMARIES_BT470_M = VSC_PRIMARIES_BT470_M
    PRIMARIES_BT470_BG = VSC_PRIMARIES_BT470_BG
    PRIMARIES_ST170_M = VSC_PRIMARIES_ST170_M
    PRIMARIES_ST240_M = VSC_PRIMARIES_ST240_M
    PRIMARIES_FILM = VSC_PRIMARIES_FILM
    PRIMARIES_BT2020 = VSC_PRIMARIES_BT2020
    PRIMARIES_ST428 = VSC_PRIMARIES_ST428
    PRIMARIES_ST431_2 = VSC_PRIMARIES_ST431_2
    PRIMARIES_ST432_1 = VSC_PRIMARIES_ST432_1
    PRIMARIES_EBU3213_E = VSC_PRIMARIES_EBU3213_E


# Alias for deprecated type name, remove this in 2030 or so
ColorRange = Range


globals().update(MediaType.__members__)
globals().update(ColorFamily.__members__)
globals().update(SampleType.__members__)
globals().update(PresetVideoFormat.__members__)
globals().update(FilterMode.__members__)
globals().update(AudioChannels.__members__)
globals().update(MessageType.__members__)
globals().update(CoreCreationFlags.__members__)
globals().update(Range.__members__)
globals().update(ChromaLocation.__members__)
globals().update(FieldBased.__members__)
globals().update(MatrixCoefficients.__members__)
globals().update(TransferCharacteristics.__members__)
globals().update(ColorPrimaries.__members__)