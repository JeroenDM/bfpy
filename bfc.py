import sys

def compile_brainfuck(source_code):
    # Filter out non-brainfuck characters
    code = "".join([c for c in source_code if c in "><+-.,[]"])

    asm = [
        ".section __TEXT,__text,regular,pure_instructions",
        ".global _main",
        ".align 2",
        "_main:",
        "    stp x29, x30, [sp, #-16]!",  # Save frame pointer and link register
        "    adrp x19, _tape@PAGE",        # Load page address of tape
        "    add x19, x19, _tape@PAGEOFF", # Add page offset
    ]

    label_stack = []
    label_count = 0

    for char in code:
        if char == '>':
            asm.append("    add x19, x19, #1")
        elif char == '<':
            asm.append("    sub x19, x19, #1")
        elif char == '+':
            asm.append("    ldrb w0, [x19]")
            asm.append("    add w0, w0, #1")
            asm.append("    strb w0, [x19]")
        elif char == '-':
            asm.append("    ldrb w0, [x19]")
            asm.append("    sub w0, w0, #1")
            asm.append("    strb w0, [x19]")
        elif char == '.':
            # syscall: write(1, x19, 1)
            asm.append("    mov x0, #1")      # fd = stdout
            asm.append("    mov x1, x19")     # buffer = current tape pointer
            asm.append("    mov x2, #1")      # length = 1
            asm.append("    mov x16, #4")     # macOS write syscall
            asm.append("    svc #0x80")
        elif char == ',':
            # syscall: read(0, x19, 1)
            asm.append("    mov x0, #0")      # fd = stdin
            asm.append("    mov x1, x19")     # buffer
            asm.append("    mov x2, #1")      # length
            asm.append("    mov x16, #3")     # macOS read syscall
            asm.append("    svc #0x80")
        elif char == '[':
            label_count += 1
            start_label = f"L_start_{label_count}"
            end_label = f"L_end_{label_count}"
            label_stack.append((start_label, end_label))
            asm.append(f"{start_label}:")
            asm.append("    ldrb w0, [x19]")
            asm.append("    cbz w0, " + end_label)
        elif char == ']':
            start_label, end_label = label_stack.pop()
            asm.append(f"    b {start_label}")
            asm.append(f"{end_label}:")

    # Exit sequence
    asm.append("    mov x0, #0")              # Return 0
    asm.append("    ldp x29, x30, [sp], #16") # Restore pointers
    asm.append("    ret")

    # Data section for the tape
    asm.append(".section __DATA,__data")
    asm.append(".align 3")
    asm.append("_tape:")
    asm.append("    .zero 30000")

    return "\n".join(asm)

with open(sys.argv[1]) as f:
    bf_code = f.read()
    output_asm = compile_brainfuck(bf_code)

with open("output.s", "w") as f:
    f.write(output_asm)
