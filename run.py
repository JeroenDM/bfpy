import subprocess
import platform
import os
import sys

ASM_FILE = "./build/output.asm"
EXE_FILE = "./build/a.out"

def run_command(cmd):
    """Executes a shell command and prints errors if they occur."""
    # print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error:\n{result.stderr}")
        sys.exit(1)
    return result.stdout

def build():
    print("--- assembling and linking ---")
    os_name = platform.system().lower()

    if not os.path.exists(ASM_FILE):
        print(f"Error: {ASM_FILE} not found. Run your compiler script first!")
        return

    if os_name == "darwin":  # macOS
        print("Detected macOS (ARM64/x86_64)...")
        run_command(["clang", "-arch", "arm64", ASM_FILE, "-o", EXE_FILE])

    elif os_name == "linux":
        print("Detected Linux (x86_64)...")
        run_command(["nasm", "-f", "elf64", ASM_FILE, "-o", "output.o"])
        run_command(["ld", "output.o", "-o", EXE_FILE])
        if os.path.exists("output.o"):
            os.remove("output.o")

    else:
        print(f"Unsupported OS: {os_name}")
        return

    print(f"\nSuccessfully created {EXE_FILE}!")
    # print(f"Run it with: {EXE_FILE}")

def run():
    print("--- running it! ---")
    print(" -- start --")
    print(run_command([EXE_FILE]), end="")
    print(" -- end   --")

if __name__ == "__main__":
    build()
    run()
