import sys

def find_matching_bracket(program, ptr, direction):
    open_bracket = "[" if direction == 1 else "]"
    close_bracket = "]" if direction == 1 else "["
    assert(program[ptr] == open_bracket)
    depth = 1
    ptr += direction
    while depth > 0:
        if ptr < 0 or ptr >= len(program):
            raise RuntimeError(f"No matching '{close_bracket}' found")
        if program[ptr] == open_bracket:
            depth += 1
        elif program[ptr] == close_bracket:
            depth -= 1
        if depth > 0:
            ptr += direction
    return ptr

def move_forward(program, inst_ptr):
    return find_matching_bracket(program, inst_ptr, 1)

def move_backward(program, ptr):
    return find_matching_bracket(program, ptr, -1)

class State:
    def __init__(self):
        self.iptr = 0  # instruction pointer
        self.dptr = 0  # data pointer into 'self.tape'
        self.tape = [0] * 1000 # TODO handle dynamic size

def step(s : State, program, io):
    cmd = program[s.iptr]
    if cmd == ">":
        s.dptr += 1
        if s.dptr >= len(s.tape):
            s.tape.append(0)
    elif cmd == "<":
        s.dptr -= 1
        if s.dptr < 0:
            raise RuntimeError("Cannot move data pointer below 0.")
    elif cmd == "+":
        s.tape[s.dptr] = (s.tape[s.dptr] + 1) % 256
    elif cmd == "-":
        s.tape[s.dptr] = (s.tape[s.dptr] - 1) % 256
    elif cmd == ".":
        io.stdout.write(chr(s.tape[s.dptr]))
    elif cmd == ",":
        ch = io.stdin.read(1)
        s.tape[s.dptr] = ord(ch) if ch else 0
    elif cmd == "[":
        if s.tape[s.dptr] == 0:
            s.iptr = move_forward(program, s.iptr)
    elif cmd == "]":
        if s.tape[s.dptr] != 0:
            s.iptr = move_backward(program, s.iptr)

    s.iptr += 1

def step_in_debugger(program: str, s : State, io):
    s.iptr = 0
    should_continue = False
    while s.iptr < len(program):
        command = input(f"{s.iptr} ({program[s.iptr]}) {s.tape[:5]} @ ")
        if should_continue or command == "s":
            step(s, program, io)
        elif command == "p":
            print(f">>[{s.iptr}] {program[s.iptr]} dptr: {s.dptr} tape:{s.tape[:5]}")
        elif command == "c":
           should_continue = True
           break
        elif command == "q":
            return ""
        else:
            print(f"Unkown command '{command}' s=step, p=print, q=quit")

    if should_continue:
        while s.iptr < len(program):
            step(s, program)


def step_until_end(program : str, s : State, io):
    s.iptr = 0
    while s.iptr < len(program):
        step(s, program, io)

def run_repl(debug):
    state = State()
    while True:
        prog = input("$ ")
        if prog == "q":
            return
        print(f"running: '{prog}'")
        if debug:
            step_in_debugger(prog, state, sys)
        else:
            step_until_end(prog, state, sys)
        print(f"tape: [{state.tape[:10]}")

def run_normal(prog):
   state = State()
   out = step_until_end(prog, state, sys)
   print(f"tape: [{state.tape[:10]}")
   print(f"output: '{out}'")


def main():
    HELLO = "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++."
    mode = "normal"
    debug = False
    prog = ""
    if  "-r" in sys.argv:
        mode = "repl"
    elif "-d" in sys.argv:
        debug = True
    elif "-f" in sys.argv:
        idx = sys.argv.index("-f")
        filepath = sys.argv[idx + 1]
        with open(filepath) as f:
            prog = f.read()
            run_normal(prog)
            return
    try:
        if mode == "repl":
            run_repl(debug)
        else:
            run_normal(HELLO)
    except KeyboardInterrupt:
        pass



if __name__ == "__main__":
    main()


def test_move_forward():
    import pytest

    assert(move_forward("[]+", 0) == 1)
    assert(move_forward(">>[+++]-", 2) == 6)
    assert(move_forward("[[[]]]", 0) == 5)
    assert(move_forward("[[[]]]", 1) == 4)
    with pytest.raises(RuntimeError):
        move_forward("[++", 0)

def test_move_backward():
    import pytest

    assert(move_backward("[]+", 1) == 0)
    assert(move_backward(">>[+++]-", 6) == 2)
    assert(move_backward("[[[]]]", 5) == 0)
    assert(move_backward("[[[]]]", 4) == 1)
    with pytest.raises(RuntimeError):
        move_backward("+]+", 1)
