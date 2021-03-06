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


import argparse
import json
import subprocess
from pathlib import Path
from typing import List, Optional

import requests

import yaml


def coloredprint(txt, color):
    """
    Print a colored line

    :param txt: The text to print.
    :param color: The "color" to use.
    :return:
    """
    colors = {"HEADER": "\033[95m", "OKBLUE": "\033[94m",
              "OKGREEN": "\033[92m", "WARNING": "\033[93m",
              "FAIL": "\033[91m", "ENDC": "\033[0m",
              "BOLD": "\033[1m", "UNDERLINE": "\033[4m"}
    print("{}{}{}".format(colors[color], txt, colors["ENDC"]))


def printoutput(stdout: List[bytes], stderr: List[bytes], failed: bool):
    """
    For debugging purposes. Does some weird color stuff, so the stdout
    and stderr from singularity are slightly easier to distinguish from
    this script's stdout/stderr.

    :param stdout: The stdout of each attempt.
    :param stderr: The stderr of each attempt.
    :param failed: Whether or not the last attempt failed.
    :return:
    """
    print("_" * 79)
    for i in range(len(stdout)):
        color = "OKBLUE" if i == len(stdout) - 1 and not failed else "WARNING"
        coloredprint("Attempt {}:".format(i + 1), "HEADER")
        coloredprint("STDERR:", color)
        print(str(stderr[i], "UTF-8"))
        coloredprint("STDOUT:", color=color)
        print(str(stdout[i], "UTF-8"))
    print("_" * 79)


def pullimage(image: str, maxattempts: int = 3, prefix: str = "docker://",
              singularityexe: str = "singularity",
              showoutputonfailure: bool = True,
              showoutputonsuccess: bool = False) -> bool:
    """
    Pull a singularity image, retrying on failures.

    :param image: The image to pull.
    :param maxattempts: The maximum amount of times to try pulling the
    image.
    :param prefix: A prefix to the image url.
    :param singularityexe: The singularity executable.
    :param showoutputonfailure: Whether or not to show the output if
    pulling fails.
    :param showoutputonsuccess: Whether or not to show the output if
    pulling succeeds.
    :return:
    """
    command = [singularityexe, "exec", "-e", "{}{}".format(prefix, image),
               "echo", "Success!"]
    attempt = 0
    rc = 1  # So the loop will run at least once
    stdout = []
    stderr = []
    while rc != 0 and attempt < maxattempts:
        attempt += 1
        proc = subprocess.run(command, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        stdout.append(proc.stdout)
        stderr.append(proc.stderr)
        rc = proc.returncode
    if rc == 0:
        coloredprint("Successfully pulled '{}{}' in {} attempt{}".format(
            prefix, image, attempt, "s" if attempt > 1 else ""), "OKGREEN")
        if showoutputonsuccess:
            printoutput(stdout, stderr, False)
        return True
    else:
        coloredprint("Failed to pull '{}{}' after {} attempt{}".format(
            prefix, image, attempt, "s" if attempt > 1 else ""), "FAIL")
        if showoutputonfailure:
            printoutput(stdout, stderr, True)
        return False


def getdigestfromquay(image: str, tag: str) -> Optional[str]:
    """
    :param image: The name of the image to retrieve the digest for.
    :param tag: The tah to retrieve the digest for
    :return: The digest or None (if the digest couldn't be retrieved)
    """
    url = "https://quay.io/api/v1/repository/{}/tag/?specificTag={}".format(
        image, tag)
    response = requests.get(url)
    if response.status_code == 200:
        try:
            content = json.loads(response.content.decode())
            return content["tags"][0]["manifest_digest"]
        except (KeyError, IndexError):
            pass
    coloredprint("Couldn't retrieve digest from Quay.io for "
                 "'quay.io/{}:{}'".format(image, tag), "FAIL")
    return None


def getdigestfromdockerhub(image: str, tag: str) -> Optional[str]:
    """
    :param image: The name of the image to retrieve the digest for.
    :param tag: The tah to retrieve the digest for
    :return: The digest or None (if the digest couldn't be retrieved)
    """
    if "/" not in image:
        image = "library/{}".format(image)
    authurl = ("https://auth.docker.io/token?service=registry.docker.io"
               "&scope=repository:{}:pull").format(image)
    authresponse = requests.get(authurl)
    if authresponse.status_code == 200:
        token = json.loads(authresponse.content.decode())["access_token"]
        url = "https://registry-1.docker.io/v2/{}/manifests/{}".format(image,
                                                                       tag)
        response = requests.get(url, headers={
            "Authorization": "Bearer {}".format(token),
            "Accept": "application/vnd.docker.distribution.manifest.v2+json"
        })
        if response.status_code == 200:
            try:
                headers = response.headers
                return headers["Docker-Content-Digest"]
            except KeyError:
                pass
    coloredprint("Couldn't retrieve digest from dockerhub for "
                 "'{}:{}'".format(image, tag), "FAIL")
    return None


def taggedimagetodigest(image: str) -> Optional[str]:
    """
    :param image: The tagged image
    :return: The image with its digest
    """
    img = image.split(":")
    imagename = img[0]
    try:
        tag = img[1]
    except IndexError:
        tag = "latest"
    if image.startswith("quay.io/"):
        imagedigest = getdigestfromquay("/".join(
            imagename.split("/")[1:]), tag)
    else:
        imagedigest = getdigestfromdockerhub(imagename, tag)
    if imagedigest is not None:
        return "{}@{}".format(imagename, imagedigest)
    else:
        return None


def parsearguments():
    parser = argparse.ArgumentParser(
        description="Pull images from listed in a YAML file, so they get "
                    "cached and can be run without pulling later.")
    parser.add_argument("input", type=Path,
                        help="A YAML file listing the images to be pulled, "
                             "either as a map or list.")
    parser.add_argument("-a", "--max-attempts", type=int, default=3,
                        help="Maximum number of times to attempt pulling "
                             "each image; defaults to 3.")
    parser.add_argument("-p", "--prefix", type=str, default="docker://",
                        help="Prefix for the image url; defaults to "
                             "'docker://'.")
    parser.add_argument("--stop-on-failure", action="store_true",
                        help="Stop when pulling an image fails; by default "
                             "all images will be attempted to be pull even "
                             "if one fails.")
    parser.add_argument("--show-output-on-failure", action="store_true",
                        help="Print the stderr and stdout when pulling an "
                             "image fails.")
    parser.add_argument("--show-output-on-success", action="store_true",
                        help="Print the stderr and stdout when pulling an "
                             "image succeeds.")
    parser.add_argument("--singularity-exe", type=str, default="singularity",
                        help="The command for running singularity; defaults "
                             "to 'singularity'")
    parser.add_argument("--use-digest", action="store_true",
                        help="Retrieve the image digestes from dockerhub or "
                             "quay.io and use those (instead of the tags) "
                             "to pull the images. Only usable with docker "
                             "images.")
    args = parser.parse_args()
    if args.max_attempts < 1:
        parser.error("max-attempts should be at least 1")
    if args.use_digest and args.prefix != "docker://":
        parser.error("use-digest only works with docker images")
    return args


def main():
    args = parsearguments()
    with args.input.open("r") as imagesfile:
        images = yaml.load(imagesfile, Loader=yaml.FullLoader)
        if type(images) == dict:
            images = images.values()
    successes = []
    for image in images:
        if not isinstance(image, str):
            raise ValueError("'{0}' is not a string".format(str(image)))

        if args.use_digest and "@" not in image:
            imagetopull = taggedimagetodigest(image)
        else:
            imagetopull = image

        if imagetopull is not None:
            successes.append(
                pullimage(imagetopull, args.max_attempts, args.prefix,
                          args.singularity_exe, args.show_output_on_failure,
                          args.show_output_on_success))
        else:
            successes.append(False)
        if args.stop_on_failure and not successes[-1]:
            exit(1)
    if False in successes:
        exit(1)   # If any pull failed, exit as a failure.
    else:
        exit(0)
