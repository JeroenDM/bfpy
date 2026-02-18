import subprocess
import sys
import pathlib
import time
import shutil

from bfc import compile


def build(bf_path, platform="arm64-macos"):
    """Compile a .b file to a native binary. Returns the binary path."""
    with open(bf_path) as f:
        source = f.read()

    asm = compile(source, platform)

    build_dir = pathlib.Path("build")
    build_dir.mkdir(exist_ok=True)

    name = pathlib.Path(bf_path).stem
    asm_path = build_dir / f"{name}.s"
    obj_path = build_dir / f"{name}.o"
    bin_path = build_dir / name

    asm_path.write_text(asm)

    if platform == "arm64-macos":
        subprocess.run(["as", "-o", str(obj_path), str(asm_path)], check=True)
        subprocess.run(["ld", "-o", str(bin_path), str(obj_path),
                        "-lSystem", "-syslibroot",
                        "/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk",
                        "-e", "_main"], check=True)
    else:
        raise ValueError(f"Unsupported platform for benchmarking: {platform}")

    return bin_path


def bench_python(bin_path, runs=10):
    """Simple benchmark using time.perf_counter."""
    times = []
    for i in range(runs):
        start = time.perf_counter()
        subprocess.run([str(bin_path)], stdout=subprocess.DEVNULL, check=True)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  run {i+1}/{runs}: {elapsed:.4f}s")

    print(f"\n  min: {min(times):.4f}s  avg: {sum(times)/len(times):.4f}s  max: {max(times):.4f}s")


def bench_hyperfine(bin_path):
    """Benchmark using hyperfine if available."""
    if not shutil.which("hyperfine"):
        print("hyperfine not found, skipping. Install with: brew install hyperfine")
        return
    subprocess.run(["hyperfine", "--warmup", "3", "--shell=none", str(bin_path)])


def main():
    bf_path = sys.argv[1] if len(sys.argv) > 1 else "examples/squares.b"
    print(f"Compiling {bf_path}...")
    bin_path = build(bf_path)
    print(f"Built {bin_path}\n")

    print("--- Python benchmark ---")
    bench_python(bin_path)

    # print("\n--- hyperfine ---")
    # bench_hyperfine(bin_path)


if __name__ == "__main__":
    main()
