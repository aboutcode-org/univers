#
# Copyright (c) 2019 JFrog LTD
# SPDX-License-Identifier: MIT
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

"""
    Exceptions raised and handled in Conan
    These exceptions are mapped between server (as an HTTP response) and client
    through the REST API. When an error happens in server its translated to an HTTP
    error code that its sent to client. Client reads the server code and raise the
    matching exception.

    see return_plugin.py

"""
from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from typing import Any, Callable
    try:
        from typing import Never
    except ImportError:
        from typing_extensions import Never


@contextmanager
def conanfile_remove_attr(
    conanfile: Any, names: Iterable[str], method: Callable[..., Any]
) -> Iterator[Never]:
    """remove some self.xxxx attribute from the class, so it raises an exception if used
    within a given conanfile method
    """
    original_class = type(conanfile)

    def _prop(attr_name: str) -> property:
        def _m(_):
            raise ConanException(f"'self.{attr_name}' access in '{method}()' method is forbidden")

        return property(_m)

    try:
        new_class = type(original_class.__name__, (original_class,), {})
        conanfile.__class__ = new_class
        for name in names:
            setattr(new_class, name, _prop(name))
        yield
    finally:
        conanfile.__class__ = original_class


@contextmanager
def conanfile_exception_formatter(conanfile_name: str, func_name: str) -> Iterator[Never]:
    """
    Decorator to throw an exception formatted with the line of the conanfile where the error ocurrs.
    """

    def _raise_conanfile_exc(e):
        m = _format_conanfile_exception(conanfile_name, func_name, e)
        raise ConanExceptionInUserConanfileMethod(m)

    try:
        yield
    # TODO: Move ConanInvalidConfiguration from here?
    except ConanInvalidConfiguration as exc:
        msg = "{}: Invalid configuration: {}".format(str(conanfile_name), exc)
        raise ConanInvalidConfiguration(msg)
    except AttributeError as exc:
        list_methods = [m for m in dir(list) if not m.startswith("__")]
        if (
            "NoneType" in str(exc)
            and func_name in ["layout", "package_info"]
            and any(method in str(exc) for method in list_methods)
        ):
            raise ConanException(
                "{}: {}. No default values are set for components. You are probably "
                "trying to manipulate a component attribute in the '{}' method "
                "without defining it previously".format(str(conanfile_name), exc, func_name)
            )
        else:
            _raise_conanfile_exc(exc)
    except Exception as exc:
        _raise_conanfile_exc(exc)


def _format_conanfile_exception(
    scope: str, method: Callable[..., Any], exception: BaseException
) -> str:
    """
    It will iterate the traceback lines, when it finds that the source code is inside the users
    conanfile it "start recording" the messages, when the trace exits the conanfile we return
    the traces.
    """
    import sys
    import traceback

    try:
        conanfile_reached = False
        tb = sys.exc_info()[2]
        index = 0
        content_lines = []

        while True:  # If out of index will raise and will be captured later
            # 40 levels of nested functions max, get the latest
            filepath, line, name, contents = traceback.extract_tb(tb, 40)[index]
            if "conanfile.py" not in filepath:  # Avoid show trace from internal conan source code
                if conanfile_reached:  # The error goes to internal code, exit print
                    break
            else:
                if not conanfile_reached:  # First line
                    msg = "%s: Error in %s() method" % (scope, method)
                    msg += ", line %d\n\t%s" % (line, contents)
                else:
                    msg = (
                        "while calling '%s', line %d\n\t%s" % (name, line, contents)
                        if line
                        else "\n\t%s" % contents
                    )
                content_lines.append(msg)
                conanfile_reached = True
            index += 1
    except Exception:
        pass
    ret = "\n".join(content_lines)
    ret += "\n\t%s: %s" % (exception.__class__.__name__, str(exception))
    return ret


class ConanException(Exception):
    """
    Generic conans exception
    """

    def __init__(self, *args, **kwargs):
        self.info = None
        self.remote = kwargs.pop("remote", None)
        super(ConanException, self).__init__(*args, **kwargs)

    def remote_message(self) -> str:
        if self.remote:
            return " [Remote: {}]".format(self.remote.name)
        return ""

    def __str__(self) -> str:

        msg = super(ConanException, self).__str__()

        try:
            msg = str(msg)
        except Exception:
            msg = repr(msg)

        if self.remote:
            return "{}.{}".format(msg, self.remote_message())

        return msg


class ConanReferenceDoesNotExistInDB(ConanException):
    """Reference does not exist in cache db"""

    pass


class ConanReferenceAlreadyExistsInDB(ConanException):
    """Reference already exists in cache db"""

    pass


class NoRemoteAvailable(ConanException):
    """No default remote configured or the specified remote do not exists"""

    pass


class InvalidNameException(ConanException):
    pass


class ConanConnectionError(ConanException):
    pass


class ConanOutdatedClient(ConanException):
    pass


class ConanExceptionInUserConanfileMethod(ConanException):
    pass


class ConanInvalidConfiguration(ConanExceptionInUserConanfileMethod):
    """
    This binary, for the requested configuration and package-id cannot be built
    """

    pass


class ConanMigrationError(ConanException):
    pass


# Remote exceptions #
class InternalErrorException(ConanException):
    """
    Generic 500 error
    """

    pass


class RequestErrorException(ConanException):
    """
    Generic 400 error
    """

    pass


class AuthenticationException(ConanException):  # 401
    """
    401 error
    """

    pass


class ForbiddenException(ConanException):  # 403
    """
    403 error
    """

    pass


class NotFoundException(ConanException):  # 404
    """
    404 error
    """

    def __init__(self, *args, **kwargs):
        self.remote = kwargs.pop("remote", None)
        super(NotFoundException, self).__init__(*args, **kwargs)


class UserInterfaceErrorException(RequestErrorException):
    """
    420 error
    """

    pass


EXCEPTION_CODE_MAPPING: dict[ConanException, int] = {
    InternalErrorException: 500,
    RequestErrorException: 400,
    AuthenticationException: 401,
    ForbiddenException: 403,
    NotFoundException: 404,
    UserInterfaceErrorException: 420,
}
