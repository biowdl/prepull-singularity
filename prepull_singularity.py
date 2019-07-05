import argparse
import subprocess as sp
from pathlib import Path
from typing import List

import yaml


def coloredprint(txt, color):
    """
    Print a colored line

    :param txt: The text to print.
    :param color: The "color" to use.
    :return:
    """
    colors = {"HEADER": "\033[95m", "OKBLUE": "\033[94m", "OKGREEN": "\033[92m", "WARNING": "\033[93m",
              "FAIL": "\033[91m", "ENDC": "\033[0m", "BOLD": "\033[1m", "UNDERLINE": "\033[4m"}
    print("{}{}{}".format(colors[color], txt, colors["ENDC"]))


def printoutput(stdout: List[bytes], stderr: List[bytes], failed: bool):
    """
    For debugging purposes. Does some weird color stuff, so the stdout and stderr from singularity are
    slightly easier to distinguish from this scripts stdout/stderr.

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


def pullimage(image: str, maxattempts: int = 3, prefix: str = "docker://", singularityexe: str = "singularity",
              showoutputonfailure: bool = True, showoutputonsuccess: bool = False):
    """
    Pull a singularity image, retrying on failures.

    :param image: The image to pull.
    :param maxattempts: The maximum amount of times to try pulling the image.
    :param prefix: A prefix to the image url.
    :param singularityexe: The singularity executable.
    :param showoutputonfailure: Whether or not to show the output if pulling fails.
    :param showoutputonsuccess: Whether or not to show the output if pulling succeeds.
    :return:
    """
    command = [singularityexe, "exec", "-e", "{}{}".format(prefix, image), "echo", "Success!"]
    attempt = 0
    rc = 1  # So the loop will run at least once
    stdout = []
    stderr = []
    while rc != 0 and attempt < maxattempts:
        attempt += 1
        with sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE) as proc:
            proc.wait()
            stdout.append(proc.stdout.read())
            stderr.append(proc.stderr.read())
            rc = proc.returncode
    if rc == 0:
        coloredprint("Successfully pulled '{}{}' in {} attempt{}".format(prefix, image, attempt,
                                                                         "s" if attempt > 1 else ""),
                     "OKGREEN")
        if showoutputonsuccess:
            printoutput(stdout, stderr, False)
        return True
    else:
        coloredprint("Failed to pull '{}{}' after {} attempt{}".format(prefix, image, attempt,
                                                                       "s" if attempt > 1 else ""),
                     "FAIL")
        if showoutputonfailure:
            printoutput(stdout, stderr, True)
        return False


def parsearguments():
    parser = argparse.ArgumentParser(description="Pull images from listed in a YAML file, so they get cached and can "
                                                 "be run without pulling later.")
    parser.add_argument("input", type=Path, help="A YAML file listing the images to be pulled, either as a map or "
                                                 "list.")
    parser.add_argument("-a", "--max-attempts", type=int, default=3, help="Maximum number of times to attempt pulling "
                                                                          "each image; defaults to 3.")
    parser.add_argument("-p", "--prefix", type=str, default="docker://", help="Prefix for the image url; defaults to "
                                                                              "'docker://'.")
    parser.add_argument("--stop-on-failure", action="store_true", help="Stop when pulling an image fails; by default "
                                                                       "all images will be attempted to be pull even "
                                                                       "if one fails.")
    parser.add_argument("--show-output-on-failure", action="store_true", help="Print the stderr and stdout when "
                                                                              "pulling an image fails.")
    parser.add_argument("--show-output-on-success", action="store_true", help="Print the stderr and stdout when "
                                                                              "pulling an image succeeds.")
    parser.add_argument("--singularity-exe", type=str, default="singularity", help="The command for running "
                                                                                   "singularity; defaults to "
                                                                                   "'singularity'")
    return parser.parse_args()


def main():
    args = parsearguments()
    with args.input.open("r") as imagesfile:
        images = yaml.load(imagesfile, Loader=yaml.FullLoader)
        if type(images) == dict:
            images = images.values()
    successes = []
    for image in images:
        successes.append(pullimage(image, args.max_attempts, args.prefix, args.singularity_exe,
                                   args.show_output_on_failure, args.show_output_on_success))
        if args.stop_on_failure and not successes[-1]:
            exit(1)
    if False in successes:
        exit(1)   # If any pull failed, exit as a failure.
    else:
        exit(0)


if __name__ == "__main__":
    main()
