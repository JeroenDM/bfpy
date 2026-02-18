import dataclasses
import sys
import pathlib

TAPE_SIZE = 30000

class Node:
    def __repr__(self):
        return f"{self.__class__.__name__}({vars(self)})"

@dataclasses.dataclass
class Add:
    """Increment/decrement current tape element by 'x'."""
    x : int

@dataclasses.dataclass
class Move(Node):
    """Move the data pointer to the right (>0) or left (<0)."""
    x : int

@dataclasses.dataclass
class Loop(Node):
    body : list[Node]

class GetChar(Node):
    pass

class PutChar(Node):
    pass

def compile_to_ir(code):
    """Convert BF string to initial IR list."""
    code = "".join([c for c in code if c in "><+-.,[]"])
    stack = [[]]
    for char in code:
        if char == '+': stack[-1].append(Add(1))
        elif char == '-': stack[-1].append(Add(-1))
        elif char == '>': stack[-1].append(Move(1))
        elif char == '<': stack[-1].append(Move(-1))
        elif char == '.': stack[-1].append(PutChar())
        elif char == ',': stack[-1].append(GetChar())
        elif char == '[': stack.append([])
        elif char == ']':
            inner = stack.pop()
            stack[-1].append(Loop(inner))
    return stack[0]

def fold_actions(nodes):
    """Combines +++ or >>> into single IR nodes."""
    if not nodes:
        return []
    optimized = []
    i = 0
    while i < len(nodes):
        match nodes[i]:
            case Add(v) | Move(v) as current:
                count = v
                while i + 1 < len(nodes) and type(nodes[i+1]) == type(current):
                    count += nodes[i+1].x
                    i += 1
                if count != 0:
                    optimized.append(type(current)(count))
            case Loop(body):
                optimized.append(Loop(fold_actions(body)))
            case other:
                optimized.append(other)
        i += 1
    return optimized

def indent(s):
    if s.startswith("L_"):
        return s
    else:
        return f"    {s}"

class ARM64_macOS:
    def __init__(self):
        self.label_idx = 0

    def generate_body(self, ir):
        lines = []
        for node in ir:
            match node:
                case Add(v):
                    if v > 0:
                        lines += ["ldrb w0, [x19]", f"add w0, w0, #{v}", "strb w0, [x19]"]
                    elif v < 0:
                        lines += ["ldrb w0, [x19]", f"sub w0, w0, #{-v}", "strb w0, [x19]"]
                case Move(v):
                    if v > 0:
                        lines += [f"add x19, x19, #{v}"]
                    elif v < 0:
                        lines += [f"sub x19, x19, #{-v}"]
                case PutChar():
                    # syscall: write(1, x19, 1)
                    lines += ["mov x0, #1", "mov x1, x19", "mov x2, #1", "mov x16, #4", "svc #0x80"]
                case GetChar():
                    # syscall: read(0, x19, 1)
                    lines += ["mov x0, #0", "mov x1, x19", "mov x2, #1", "mov x16, #3", "svc #0x80"]
                case Loop(body):
                    self.label_idx += 1
                    label = self.label_idx
                    lines += [f"L_start_{label}:", "ldrb w0, [x19]", f"cbz w0, L_end_{label}"]
                    lines += self.generate_body(body)
                    lines += [f"b L_start_{label}", f"L_end_{label}:"]
        return lines

    def generate(self, ir):
        asm = [
                ".section __TEXT,__text,regular,pure_instructions",
                ".global _main",
                ".align 2",
                "_main:",
                "    stp x29, x30, [sp, #-16]!",  # Save frame pointer and link register
                "    adrp x19, _tape@PAGE",  # Load page address of tape
                "    add x19, x19, _tape@PAGEOFF",  # Add page offset
        ]
        asm.extend(map(indent, self.generate_body(ir)))
        # Exit sequence
        asm.append("    mov x0, #0")  # Return 0
        asm.append("    ldp x29, x30, [sp], #16")  # Restore pointers
        asm.append("    ret")

        # Data section for the tape
        asm.append(".section __DATA,__data")
        asm.append(".align 3")
        asm.append("_tape:")
        asm.append(f"    .zero {TAPE_SIZE}")

        return "\n".join(asm)

class X86_64_Linux:
    def __init__(self): self.label_idx = 0

    def generate_body(self, ir):
        lines = []
        for node in ir:
            match node:
                case Add(v):
                    lines += [f"add byte [r12], {v}"]
                case Move(v):
                    lines += [f"add r12, {v}"]
                case PutChar():
                    # syscall: write(1, buf, 1)
                    lines += ["mov rax, 1", "mov rdi, 1", "mov rsi, r12", "mov rdx, 1", "syscall"]
                case PutChar():
                    # syscall: write(1, buf, 1)
                    lines += [
                        "mov rax, 1",      # syscall 1: write
                        "mov rdi, 1",      # fd 1: stdout
                        "mov rsi, r12",    # buffer: current tape pointer
                        "mov rdx, 1",      # length: 1 byte
                        "syscall"
                    ]

                case GetChar():
                    # syscall: read(0, buf, 1)
                    lines += [
                        "xor rax, rax",    # syscall 0: read (xor is a faster 'mov rax, 0')
                        "xor rdi, rdi",    # fd 0: stdin
                        "mov rsi, r12",    # buffer: current tape pointer
                        "mov rdx, 1",      # length: 1 byte
                        "syscall"
                    ]
                case Loop(body):
                    self.label_idx += 1
                    label = self.label_idx
                    lines += [f"L_start_{label}:", "cmp byte [r12], 0", f"je L_end_{label}"]
                    lines += self.generate_body(body)
                    lines += [f"jmp L_start_{label}", f"L_end_{label}:"]
        return lines

    def generate(self, ir):
        asm = [
            "section .text",
            "global _start",
            "_start:",
            "    mov r12, tape",
        ]
        asm.extend(map(indent, self.generate_body(ir)))
        # Exit sequence and data section
        asm.extend([
            "    mov rax, 60",
            "    xor rdi, rdi",
            "    syscall",
            "section .data",
            f"tape: times {TAPE_SIZE} db 0",
        ])

        return "\n".join(asm)



def compile(source_code, platform):
    # Filter out non-brainfuck characters.
    code = "".join([c for c in source_code if c in "><+-.,[]"])

    # Generate intermediate representation that we can optimize.
    ir = compile_to_ir(code)
    ir = fold_actions(ir)

    if platform == "arm64-macos":
        backend = ARM64_macOS()
    elif platform == "x86-64-linux":
        backend = X86_64_Linux()
    else:
        raise ValueError(f"Unknow platform: '{platform}")

    return backend.generate(ir)


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        bf_code = f.read()

        platform = "x86-64-linux"
        if "-p" in sys.argv:
            idx = sys.argv.index("-p")
            platform = sys.argv[idx + 1]


        output_asm = compile(bf_code, platform)



    build_dir = pathlib.Path("build")
    if not build_dir.exists():
        print(f"Creating directory: {build_dir}")
        build_dir.mkdir(parents=True)

    with open("build/output.asm", "w") as f:
        f.write(output_asm)


def test_hello(snapshot):
    HELLO = "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++."
    assert snapshot == compile(HELLO, platform="arm64-macos")
    assert snapshot == compile(HELLO, platform="x86-64-linux")


def test_echo(snapshot):
    ECHO = ",[.,]"
    assert snapshot == compile(ECHO, platform="arm64-macos")
    assert snapshot == compile(ECHO, platform="x86-64-linux")
