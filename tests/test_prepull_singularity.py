# Copyright (c) 2019 Leiden University Medical Center
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from prepull_singularity import (coloredprint, getdigestfromdockerhub,
                                 getdigestfromquay)


def test_getdigestfromdockerhub():
    digest = getdigestfromdockerhub("biocontainers/cpat", "v1.2.4_cv2")
    assert digest == ("sha256:6ee77007a59b331a31203ac68c20855230f3e64be550ace8"
                      "8645c63550060b90")


def test_getdigestfromquay():
    digest = getdigestfromquay("biocontainers/samtools", "1.2-0")
    assert digest == ("sha256:97b9627711c16125fe1b57cf8745396064fd88ebeff6ab00"
                      "cf6a68aeacecfcda")


def test_coloredprint(capsys):
    coloredprint("underlined", "UNDERLINE")
    captured = capsys.readouterr()
    assert captured.out == "\033[4munderlined\033[0m\n"
