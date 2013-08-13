# Copyright 2013 Agustin Henze <tin@sluc.org.ar>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import fnmatch
import os
from os.path import join, normpath, abspath, relpath, basename, dirname
from dlt import utils


class Coverage(object):
    def __init__(self, paragraphs, directory):
        self._paragraphs = paragraphs
        self._directory = directory
        self._unmatch = set()
        self._match = {}

    def show_msg(self):
        if len(self._unmatch) > 0:
            print('The files listed below are not associated with any license')
        for filename_unmatch in self._unmatch:
            print('\t{}'.format(filename_unmatch))

    def get_rule_associated(self, filename):
        filename = abspath(normpath(filename))
        root = relpath(dirname(filename), self._directory)
        filename = join(root, basename(filename))
        match = fnmatch.filter(self._match.keys(), filename)
        if match:
            return self._match[match[0]]
        return None


    def apply(self):
        self._get_matches()
        return not bool(len(self._unmatch))

    def _get_matches(self):
        paragraphs = []
        for paragraph in utils.get_by_type(self._paragraphs, "files"):
            paragraphs.append((paragraph, paragraph.patterns))
        for root, dirs, files in os.walk(self._directory, topdown=True):
            root = relpath(root, self._directory)
            paths = [join(root, filename) for filename in files]
            self._unmatch |= set(paths)
            for paragraph, patterns in paragraphs:
                for pattern in patterns:
                    goodfiles = []
                    if pattern.find(os.path.sep) == -1:
                        pattern_norm = os.path.join(os.path.curdir, pattern)
                        goodfiles.extend(fnmatch.filter(paths, pattern_norm))
                    goodfiles.extend(fnmatch.filter(paths, pattern))
                    self._unmatch -= set(goodfiles)
                    self._match.update({f: paragraph for f in goodfiles})
