import os
import shutil
import subprocess

is_windows = os.name == "nt"

def build_rust(build_args, out_name):
    print("Building", out_name)

    subprocess.run(
        ["cargo", "build", "--release"] + build_args,
        cwd="bootloader",
        check=True,
    )

    
    exe_name = "bootloader" + (".exe" if is_windows else "")

    src = os.path.join(
        "bootloader",
        "target",
        "release",
        exe_name,
    )

    dst = os.path.join('EXEs', out_name + (".exe" if is_windows else ""))

    shutil.copy2(src, dst)


def main():
    shutil.rmtree('EXEs', ignore_errors=True)
    os.makedirs('EXEs')
    build_rust(["--features", "console"], "bootloader")
    build_rust(["--no-default-features"], "bootloaderw")

if __name__ == "__main__":
    main()
