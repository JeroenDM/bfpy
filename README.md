# Brainf**k interpreter / compiler


## Interpreter

```bash
uv run bf.py examples/hello.b
```


## Compiler

```bash
uv run bfc.py examples/hello.b -p "x86-64-linux"
uv run bfc.py examples/hello.b -p "arm64-macos"
```

```bash
uv run run.py
```

## Microservices


Writing bf programs if fing* hard. I did not write any of the programs in the examples folder myself. How can I enable a mere mortal like me to write bf programs? Microservices! Or, get modularity I just organize hunderds of bf programs in a directed acyclic graph where the nodes are connected through stdout/stdin. This allows me to only write very simple bf programs. Only upsides, let's go!


Specs:

- Only directed acyclic graph (DAG) is allowed for now.
- Programs are started in topologically sorted order.


Example config for a voting program:

```json
{
"nodes": [
  {"name": "fan_out", "exe": "fan_out"},
  {"name": "A", "exe": "has_a"},
  {"name": "B", "exe": "has_b"},
  {"name": "C", "exe": "has_c"},
  {"name": "vote", "exe": "vote"},
  {"name": "not", "exe": "logical_not"},
],
"edges": [
  {"src": "fan_out", "dst": "A"},
  {"src": "fan_out", "dst": "B"},
  {"src": "fan_out", "dst": "C"},
  {"src": "A", "dst": "vote"},
  {"src": "B", "dst": "vote"},
  {"src": "C", "dst": "vote"},
  {"src": "vote", "dst": "logical_not"},
]
}
```
