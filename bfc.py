import dataclasses
import sys

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
    steps : int

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

class ARM64_macOS:
    def __init__(self):
        self.label_idx = 0

    def generate(self, ir):
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
                    lines += self.generate(body)
                    lines += [f"b L_start_{label}", f"L_end_{label}:"]
        return lines

def indent(s):
    if s.startswith("L_"):
        return s
    else:
        return f"    {s}"

def compile(source_code):
    # Filter out non-brainfuck characters.
    code = "".join([c for c in source_code if c in "><+-.,[]"])


    # Generate intermediate representation that we can optimize.
    ir = compile_to_ir(code)

    asm = [
            ".section __TEXT,__text,regular,pure_instructions",
            ".global _main",
            ".align 2",
            "_main:",
            "    stp x29, x30, [sp, #-16]!",  # Save frame pointer and link register
            "    adrp x19, _tape@PAGE",  # Load page address of tape
            "    add x19, x19, _tape@PAGEOFF",  # Add page offset
    ]
    cmp = ARM64_macOS()
    asm.extend(map(indent,cmp.generate(ir)))

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


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        bf_code = f.read()
        output_asm = compile(bf_code)


        ir = compile_to_ir(bf_code)
        for line in ir:
            print(line)

    with open("output.s", "w") as f:
        f.write(output_asm)


def test_hello(snapshot):
    HELLO = "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++."
    assert snapshot == compile(HELLO)


def test_echo(snapshot):
    ECHO = ",[.,]"
    assert snapshot == compile(ECHO)
