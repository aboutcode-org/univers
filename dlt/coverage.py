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
from dlt import utils


class Coverage(object):
    def __init__(self, paragraphs, directory):
        self._paragraphs = paragraphs
        self._directory = directory
        self._unmatch = set()

    def show_msg(self):
        if len(self._unmatch) > 0:
            print('The files listed below are not associated with any license')
        for filename_unmatch in self._unmatch:
            print('\t{}'.format(filename_unmatch))

    def get_rule_associated(self, filename):
        filename = os.path.abspath(os.path.normpath(filename))
        root = os.path.relpath(os.path.dirname(filename), self._directory)
        filename = os.path.join(root, os.path.basename(filename))
        for paragraph in utils.get_by_type(self._paragraphs, "files"):
            if fnmatch.filter(paragraph.match, filename):
                return paragraph

    def apply(self):
        self._get_matches()
        return bool(len(self._unmatch))

    def _get_matches(self):
        paragraphs = []
        for paragraph in utils.get_by_type(self._paragraphs, "files"):
            paragraphs.append((paragraph, paragraph.patterns))
            paragraph.match = []
        for root, dirs, files in os.walk(self._directory, topdown=True):
            root = os.path.relpath(root, self._directory)
            paths = [os.path.join(root, filename) for filename in files]
            self._unmatch |= set(paths)
            for paragraph, patterns in paragraphs:
                for pattern in patterns:
                    goodfiles = fnmatch.filter(paths, pattern)
                    self._unmatch -= set(goodfiles)
                    #goodfiles = [os.path.normpath(f) for f in goodfiles]
                    paragraph.match.extend(goodfiles)
