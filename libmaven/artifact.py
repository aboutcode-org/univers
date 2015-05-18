#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""
The artifact module provides objects and functions for working with artifacts
in a maven repository
"""

import re

from .errors import ArtifactParseError
from .versioning import VersionRange


MAVEN_COORDINATE_RE = re.compile(
    r'(?P<group_id>[^:]+)'
    r':(?P<artifact_id>[^:]+)'
    r'(:(?P<type>[^:]+)(:(?P<classifier>[^:]+))?)?'
    r':(?P<version>[^:])'
    )

class Artifact(object):
    """Represents an artifact within a maven repository."""
    def __init__(self, group_id, artifact_id, version, type=None,
                 scope=None, classifier=None):
        if type is None:
            type = "jar"

        self.group_id = group_id
        self.artifact_id = artifact_id
        if isinstance(version, str):
            version = VersionRange.fromstring(version)
        self.version = version
        self.type = type
        self.scope = scope
        self.classifier = classifier

    def __cmp__(self, other):
        if self is other:
            return 0

        if not isinstance(other, Artifact):
            return -1

        result = cmp(self.group_id, other.group_id)
        if result == 0:
            result = cmp(self.artifact_id, other.artifact_id)

            if result == 0:
                result = cmp(self.type, other.type)

                if result == 0:
                    if self.classifier is None:
                        if other.classifier is not None:
                            result = 1
                    else:
                        if other.classifier is None:
                            result = -1
                        else:
                            result = cmp(self.classifier, other.classifier)

                    if result == 0:
                        result = cmp(self.version.version, other.version.version)

        return result

    def __str__(self):
        s = ':'.join((self.group_id, self.artifact_id, self.type))
        if self.classifier:
            s += ':' + self.classifier
        if self.version.version:
            s += ':' + str(self.version.version)
        else:
            s += ':' + str(self.version)

        if self.scope is not None:
            s += ':' + self.scope
        return s

    def __repr__(self):
        return "<pymaven.Artifact(%s, %s, %s, %s, %s, %s)" % (
            self.group_id,
            self.artifact_id,
            self.version,
            self.type,
            self.scope,
            self.classifier,
            )

    @property
    def coordinate(self):
        return (self.group_id, self.artifact_id, self.version, self.type,
                self.classifier)

    @staticmethod
    def fromstring(coordinate):
        """Create an artifact from a string coordinate

        :param str coordinate: match the form group:artifact[:packaging[:classifier]]:version
        :return: Artifact matching the coordinate
        :rtype: pymaven.Artifact
        """
        m = MAVEN_COORDINATE_RE.match(coordinate)
        if not m:
            raise ArtifactParseError("Invalid coordinate: %s" % coordinate)
        return Artifact(**m.groupdict())

    @property
    def path(self):
        path = "/%s/%s" % (self.group_id.replace('.', '/'), self.artifact_id)

        version = self.version.version
        if version:
            path += "/%s/%s-%s" % (version, self.artifact_id, version)
            if self.classifier:
                path += "-%s" % self.classifier
            path += ".%s" % self.type
        return path
