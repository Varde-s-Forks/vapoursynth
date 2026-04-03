from __future__ import annotations

import enum
import inspect
import keyword
import typing

if typing.TYPE_CHECKING:
    from ._main import AudioNode, VideoNode


def _construct_type(signature: str) -> typing.Any:
    from ._main import AudioFrame, AudioNode, Func, VideoFrame, VideoNode

    type_, *opt = signature.split(":")

    # Handle Arrays.
    if type_.endswith("[]"):
        array = True
        type_ = type_[:-2]
    else:
        array = False

    # Handle types
    if type_ == "vnode":
        type_ = VideoNode
    elif type_ == "anode":
        type_ = AudioNode
    elif type_ == "vframe":
        type_ = VideoFrame
    elif type_ == "aframe":
        type_ = AudioFrame
    elif type_ == "func":
        type_ = typing.Union[Func, typing.Callable]
    elif type_ == "int":
        type_ = int
    elif type_ == "float":
        type_ = float
    elif type_ == "data":
        type_ = typing.Union[str, bytes, bytearray]
    else:
        type_ = typing.Any

    # Make the type_ a sequence.
    if array:
        type_ = typing.Union[type_, typing.Sequence[type_]]

    # Mark an optional type_
    if opt:
        type_ = typing.Optional[type_]

    return type_


def _construct_parameter(signature: str) -> inspect.Parameter:
    if signature == "any":
        return inspect.Parameter("kwargs", inspect.Parameter.VAR_KEYWORD, annotation=typing.Any)

    name, signature = signature.split(":", 1)

    if keyword.iskeyword(name):
        name += "_"

    type_ = _construct_type(signature)

    _, *opt = signature.split(":")

    if opt:
        default_value = None
    else:
        default_value = inspect.Parameter.empty

    return inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=default_value, annotation=type_)


def construct_signature(
    signature: str,
    return_signature: str,
    injected: AudioNode | VideoNode | None = None,
    name: str | None = None,
) -> inspect.Signature:
    params = list(_construct_parameter(param) for param in signature.split(";") if param)

    if injected and params:
        params.pop(0)

    return_annotations = list(_construct_parameter(rparam) for rparam in return_signature.split(";") if rparam)

    if not return_annotations:
        return_annotation = None
    elif len(return_annotations) == 1:
        return_annotation = return_annotations.pop().annotation
    else:
        ret_dict_name = f"_ReturnDict_{name}" if name else "_ReturnDict"
        fields = {ret_ann.name: ret_ann.annotation for ret_ann in return_annotations}
        return_annotation = typing.TypedDict(ret_dict_name, fields) # pyright: ignore[reportArgumentType]
        return_annotation.__module__ = Exception.__module__

    return inspect.Signature(tuple(params), return_annotation=return_annotation)


def _construct_repr_wrap(value: typing.Any) -> typing.Any:
    from ._main import VideoFormat

    if isinstance(value, (enum.Enum, VideoFormat)):
        return value.name

    if isinstance(value, typing.Iterator):
        value = ", ".join(_construct_repr_wrap(v) for v in value)

    to_wrap = isinstance(value, str) and not value.startswith("<") and " " in value

    if to_wrap:
        return f'"{value}"'

    return value


def _construct_repr(obj: object, **kwargs: typing.Any) -> str:
    address = f"{id(obj):X}".rjust(16, "0")

    add_data = ""

    if kwargs:
        add_data += ", ".join(f"{key}={_construct_repr_wrap(value)}" for key, value in kwargs.items())
        add_data = f" {add_data}"

    return f"<{obj.__class__.__module__}.{obj.__class__.__qualname__} object at 0x{address}{add_data}>"
