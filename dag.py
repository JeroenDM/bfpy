import subprocess

# 1. Start both processes (Non-blocking)
proc1 = subprocess.Popen(
    ["./node_a"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
)
proc2 = subprocess.Popen(
    ["./node_b"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
)

# 2. Send input data (if needed)
# Note: Using communicate() here is okay because it handles the
# I/O and then waits, but since both are already running,
# they are executing in parallel.
out1, err1 = proc1.communicate(input="data_for_a")
out2, err2 = proc2.communicate(input="data_for_b")

# 3. Use the results
print(f"Node A said: {out1}")
print(f"Node B said: {out2}")
