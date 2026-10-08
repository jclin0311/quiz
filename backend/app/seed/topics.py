# The 12 topic lists from "如何科学刷题" (leetcode.cn/discuss/post/3141566).
# (id, name, x, y) — x/y are layout positions on a 0-100 grid.
TOPICS = [
    ("sliding-window", "Sliding Window & Two Pointers", 50, 3),
    ("binary-search", "Binary Search", 50, 18),
    ("bit-manipulation", "Bit Manipulation", 84, 18),
    ("data-structures", "Data Structures", 50, 33),
    ("trees", "Linked Lists, Trees & Backtracking", 50, 48),
    ("monotonic-stack", "Monotonic Stack", 16, 48),
    ("strings", "Strings", 84, 48),
    ("grid", "Grid Graphs", 50, 63),
    ("dp", "Dynamic Programming", 50, 78),
    ("graphs", "Graph Algorithms", 84, 78),
    ("greedy", "Greedy & Thinking", 30, 93),
    ("math", "Math", 70, 93),
]

# Core route, steps 1-7 (step 0 is programming basics; trees covers steps 4 and 6).
CORE_ROUTE = ["sliding-window", "binary-search", "data-structures", "trees", "grid", "dp"]

# (prerequisite, dependent): the core route in order, then each remaining list
# after the core topic it builds on.
EDGES = [
    *zip(CORE_ROUTE, CORE_ROUTE[1:]),
    ("sliding-window", "bit-manipulation"),
    ("data-structures", "monotonic-stack"),
    ("data-structures", "strings"),
    ("grid", "graphs"),
    ("dp", "greedy"),
    ("dp", "math"),
]
