import subprocess

def convert_file(path):
    command = f"convert {path} -strip {path}"
    return subprocess.run(command, shell=True, check=True)
