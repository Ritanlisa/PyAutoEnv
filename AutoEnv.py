# /usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import argparse
import sys
import os
import re

inital_entry = [
    "main",
    "run",
    "gui",
    "webui",
    "launch",
    "start",
    "install",
    "inference",
    "setup",
    "server",
    "__init__",
]

cuda_allowed = {"11.8": "cu118", "12.1": "cu121"}

module_transfer = {
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "torch": "pytorch",
}


def install_by_subprocess(command, max_retry, action):
    success = False
    retry = 0
    while not success and (retry < max_retry or max_retry == -1):
        res = subprocess.call(command, stdout=subprocess.PIPE, shell=True)
        success = res == 0
        if not success:
            if "Timeout" or "timeout" or "timed out" in res.stdout:
                print(f"{action} Timeout, retrying ...")
            else:
                retry += 1
                print(f"{action} failed, retrying {retry}/{max_retry} ...")
    if success:
        print(f"{action} success")
    else:
        print(f"{action} failed after {max_retry} retries")
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("entry", help="entry point of the python file", default=None)
    parser.add_argument(
        "--conda", help="use conda environment", action="store_true", default=False
    )
    parser.add_argument(
        "--python",
        help="use pip environment",
        default="3.12",
    )
    parser.add_argument(
        "--retlenv",
        help="max retry times for creating local environment",
        default=10,
    )
    parser.add_argument(
        "--retry", help="max retry times for dealing dependencies", default=-1
    )
    parser.add_argument(
        "--cuda", help="install pytorch with cuda support", default=None
    )
    parser.add_argument(
        "--wait",
        help="wait time(s) to check if the entry program runs successfully",
        default=300,
    )
    args = parser.parse_args()

    # use README.md get file support
    readme_command = ""
    if os.path.exists("README.md"):
        print("Read README.md to get file support")
        with open("README.md", "r") as f:
            content = f.read()
        commandLine = re.search(
            r"```.*\n([.*pip.*|.*conda.*|.*install.*|.*git.*|.*requirements.*])\n```",
            content,
            re.DOTALL,
        )
        pyversion = re.search(r"```.*\n.*python[ |==](\d+\.\d+).*\n```", content)

        if pyversion != None:
            args.python = pyversion.group(1)
        if commandLine != None:
            for matchresult in commandLine.groups():
                gitName = re.search(r"git clone .*[/|:].*/(.*)", matchresult)
                if gitName != None:
                    command = matchresult.strip().replace("\n", " && ")
                    if gitName.group(1) in os.path.basename(os.getcwd()):
                        # if the git repo name is the same as the current folder, change to parent folder first
                        command = "cd .. && " + command

                # if pip install is the first command, run command after conda environment is created
                pipHeader = re.search(r"[pip|pip3] install.*", matchresult)
                if pipHeader != None:
                    readme_command += command.strip() + "\n"
                else:
                    success = install_by_subprocess(
                        command, args.retlenv, "install dependecies from README.md"
                    )
    readme_command = readme_command.strip().replace("\n", " && ")

    # select entry point
    entry = None
    use_conda = args.conda

    if args.entry != None:
        if os.path.exists(args.entry):
            entry = args.entry
        elif os.path.exists(args.entry + ".py"):
            entry = args.entry + ".py"
        elif os.path.exists(args.entry + ".pyw"):
            entry = args.entry + ".pyw"
        else:
            print(f"Error: File {args.entry} not found")
            sys.exit(1)
    else:
        vaild_py_files = [name for name in os.listdir() if name.endswith(".py")]
        valid_pyw_files = [name for name in os.listdir() if name.endswith(".pyw")]
        if len(vaild_py_files) == 1:
            entry = vaild_py_files[0]
        elif len(valid_pyw_files) == 1:
            entry = valid_pyw_files[0]
        elif len(vaild_py_files) > 1:
            for name in inital_entry:
                if name + ".py" in vaild_py_files:
                    entry = name + ".py"
                    break
        if entry == None and len(valid_pyw_files) > 1:
            for name in inital_entry:
                if name + ".pyw" in vaild_py_files:
                    entry = name + ".pyw"
                    break
        if len(vaild_py_files) == 0 and len(valid_pyw_files) == 0:
            print("Error: No python files found")
            sys.exit(1)
        if entry == None:
            print(
                "Error: Multiple python files found, please specify the entry point manually"
            )
            sys.exit(1)
        else:
            print(f"Auto selected entry point: {entry}")

    # create conda environment

    if use_conda:
        if not os.path.exists("venv"):
            success = False
            if os.path.exists("environment.yml"):
                success = install_by_subprocess(
                    "conda env create -f environment.yml",
                    args.retlenv,
                    "Create conda environment from environment.yml",
                )
            if os.path.exists("environment.yaml") and not success:
                success = install_by_subprocess(
                    "conda env create -f environment.yaml",
                    args.retlenv,
                    "Create conda environment from environment.yaml",
                )
            if not success:
                success = install_by_subprocess(
                    f"conda create --prefix ./venv python={args.python} -y",
                    args.retry,
                    "Create conda environment",
                )
            pycommand = "call conda activate ./venv && python "
        else:
            print("Conda environment already exists, skip creation")
    else:
        print("No conda environment used, using global python environment")
        pycommand = "python "

    # install dependencies from README.md
    if readme_command != "":
        success = install_by_subprocess(
            f"{pycommand} -m pip install {readme_command}",
            args.retlenv,
            "Install dependencies from README.md",
        )
    # install requirements
    if os.path.exists("requirements.txt"):

        if args.cuda != None:
            # install pytorch with cuda support
            with open("requirements.txt", "r") as f:
                if "torch" in f.read():
                    if args.cuda not in cuda_allowed:
                        print(f"Error: cuda version {args.cuda} is not supported")
                        sys.exit(1)
                    success = install_by_subprocess(
                        f"{pycommand} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/{cuda_allowed[args.cuda]}",
                        args.retlenv,
                        "Install pytorch with cuda support",
                    )

        # install normal requirements
        success = install_by_subprocess(
            f"{pycommand} -m pip install -r requirements.txt",
            args.retlenv,
            "Install requirements from requirements.txt",
        )
    else:
        print("No requirements.txt found, skip installation")

    # for all files py/pyw/ipynb in the current folder or subfolders, install dependencies from setup.py
    for root, dirs, files in os.walk("."):
        for name in files:
            if name.endswith(".py") or name.endswith(".pyw") or name.endswith(".ipynb"):
                with open(os.path.join(root, name), "r") as f:
                    match = re.search(
                        r"[import\s+(.*)\s|from\s+(.*)\simport.*]", f.read()
                    )
                    for single in match.groups():
                        if single != None:
                            module = single.split(" ")[0]
                            if module in module_transfer:
                                module = module_transfer[module]
                            result = install_by_subprocess(
                                f"{pycommand} -m pip install {module}",
                                args.retry,
                                f"Install module {module}",
                            )

    # run entry point to install additional dependencies

    wait_time = args.wait
    success = False
    retry = 0
    while not success and (retry < args.retry or args.retry == -1):
        res = subprocess.call(
            f"{pycommand} {entry}",
            stdout=subprocess.PIPE,
            shell=True,
            timeout=wait_time,
        )
        success = res == 0
        if not success and retry < args.retry:
            # if exit from timeout, take it as a success
            if f"timed out after {wait_time} seconds" in res.stdout:
                print(
                    f"Entry {entry} Timeout after {wait_time} seconds, this program will take it as a success and exit."
                )
                exit(0)
            match = re.search(
                ".*ModuleNotFoundError: No module named'(.*)'", res.stdout
            )
            if match != None:
                module = match.group(1)
                if module in module_transfer:
                    module = module_transfer[module]
                result = install_by_subprocess(
                    f"{pycommand} -m pip install {module}",
                    args.retry,
                    f"Install module {module}",
                )
                continue
            if "Timeout" or "timeout" or "timed out" in res.stdout:
                print(f"Run {entry} Timeout, retrying ...")
            else:
                retry += 1
                print(f"Run {entry} failed, retrying {retry}/{args.retry} ...")
    if success:
        print(f"Environment setup of {entry} succeed! This program will exit now.")
        exit(0)
    else:
        print(
            f"Environment setup of {entry} failed after {args.retry} retries. This program will exit now."
        )
        exit(1)
