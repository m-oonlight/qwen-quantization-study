# CORRECT

Question: HV3-TREE_DP-02 | Quantization: Q8_0 | Status: correct

Solution correct: True | Strict response correct: False

Hidden tests passed: 48/48 | First failure (index only): null

Inference seconds: 353.02311433700015 | Decode tokens/s: 33.73407407670932 | Thinking budget exhausted: None | Output cap reached: False

## Exact prompt

Algorithmic Python task. data={"n":integer 1..120,"edges":[[u,v],...]}; edges form a simple undirected tree on 0..n-1. Every edge has unit length. Pair distance counts edges.

Root the tree at vertex 0. Return a list indexed by vertex v giving the size of the subtree rooted at v, counting v itself.
Result JSON Schema: {"type":"array","items":{"type":"integer"}}. Results are graded after JSON serialization and parsing. Use Python int (not bool) for integer results, bool for booleans, list or tuple for JSON arrays, dict with string keys for objects, None for null; no NaN or infinity. Normalized JSON types and values must match exactly.
Code rules (checked automatically; breaking any rule fails the task):
- Define solve(data) and return the result. No imports, classes, decorators, file/console input or output, or network.
- The top level may contain only function definitions and names assigned a literal constant, e.g. INF=1000000000000000000 (not INF=10**18 or INF=float("inf")). No docstring, if __name__ guard or other top-level statement.
- Function default values must be literals. Helper functions are allowed.
- Do not use names beginning with two underscores, attributes beginning with an underscore, or eval, exec, open, compile, globals, locals, getattr, setattr, delattr, vars, input, breakpoint.
- Only these builtins exist: abs, all, any, bool, dict, enumerate, filter, float, int, isinstance, len, list, map, max, min, next, range, reversed, round, set, sorted, str, sum, tuple, zip, ValueError, TypeError, ord, chr, divmod, frozenset, pow, iter, repr, bin, oct, hex, format, bytes, bytearray, complex, slice, type, callable, issubclass, object, Exception, RuntimeError, IndexError, KeyError, StopIteration, ZeroDivisionError. Methods of built-in types (list, dict, str, int, ...) may be used.
- When solve returns, data must compare equal (==) to its value before the call; restoring temporary changes is fine, and the result may reuse parts of the input.
- Each test calls solve on a fresh copy of a valid input; do not rely on earlier calls.
All test cases together must finish within 10 seconds of CPU time and 20 seconds of wall-clock time.
You may show working. End with FINAL_CODE: and exactly one fenced code block defining solve(data), with nothing afterward. The opening fence may be ```python or untagged ```; literal backticks inside a Python string do not delimit the response block.

## Entire emitted thinking

The user wants a Python function `solve(data)` that takes a dictionary representing a tree and returns a list of subtree sizes for each vertex, rooted at 0.

**Input Format:**
`data` is a dictionary:
- `data["n"]`: integer $N$, where $1 \le N \le 120$.
- `data["edges"]`: list of edges, e.g., `[[u, v], ...]`. The graph is a simple undirected tree on vertices $0, \dots, n-1$. Edges have unit length (though this is just flavor text for distance, we need subtree sizes).

**Output Format:**
A list of integers. The $i$-th element (index $i$) corresponds to the size of the subtree rooted at vertex $i$. The root is 0.

**Constraints & Rules:**
- No imports.
- Only specific builtins allowed.
- No global state changes that persist or modify input in a way that affects future calls (though "compare equal" allows temporary modification if restored, it's safer not to modify `data` deeply).
- Efficiency: $N \le 120$ is very small, so even $O(N^2)$ is fine. But DFS/BFS is $O(N)$.

**Algorithm:**
1. Parse the input to build an adjacency list representation of the tree.
   - Since the input `edges` contains undirected edges `[u, v]`, for each edge, add $v$ to `adj[u]` and $u$ to `adj[v]`.
2. Perform a traversal starting from root 0 to determine parent-child relationships or simply compute subtree sizes recursively/iteratively.
   - A post-order traversal (processing children before parents) is needed to calculate subtree sizes.
   - Subtree size of $v = 1 + \sum$ (subtree size of children of $v$).

**Implementation Details:**
- **Adjacency List**: Use a list of lists. `adj = [[] for _ in range(n)]`.
- **Traversal**:
  - Iterative DFS or BFS to determine parent pointers and processing order, then compute sizes bottom-up.
  - Or just recursive DFS (Python recursion limit is usually 1000, $N \le 120$ fits easily).
  
Let's stick to the allowed builtins. `list`, `int`, `len`, `range`, etc.

**Recursive Approach:**
Function `dfs(u, p)` returns size of subtree at `u`.
Iterate over neighbors $v$ in `adj[u]`. If $v \neq p$, recurse `size = dfs(v, u)`, add to sum. Return `1 + sum`.

Wait, the function `solve` must handle the input format.
Input: `data` dict.
$n = data["n"]$
edges = `data["edges"]`

Let's construct adjacency list.
Since $N$ is small, simple loops work.

**Code Structure:**
```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    
    # Build adjacency list
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
        
    result = [0] * n
    
    # DFS to compute sizes
    # We need a stack for iterative DFS to avoid recursion limit issues? 
    # Though 120 is small. But recursion is cleaner to write.
    # Let's use recursion if allowed, but standard recursion limit is fine.
    # Wait, "Define solve(data) ... Function default values must be literals."
    # Recursive helper inside solve or outside? Outside is easier.
    
    # Let's write an iterative post-order traversal to be safe and robust.
    
    # 1. BFS/DFS to get order from root to leaves (pre-order) and parent pointers
    parent = [-1] * n
    order = [] # To store nodes in topological order (parents before children) or reverse for bottom-up
    
    stack = [0]
    visited = [False] * n
    visited[0] = True
    
    while stack:
        u = stack.pop()
        order.append(u)
        
        # Iterate neighbors
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                stack.append(v)
                
    # Now 'order' has nodes roughly top-down (actually depends on stack pop order, but it's a valid traversal).
    # Actually, standard DFS stack LIFO. 
    # If we process in reverse of the traversal order (children before parents), we can compute sizes.
    # Wait, 'order' list adds nodes as we visit them. 
    # In a tree, children are visited after parents. So reversing 'order' gives children before parents (mostly).
    # Actually, if we push to stack, we process the last pushed node first.
    # But regardless of DFS or BFS order, if we just reverse the list of visited nodes in a traversal starting from root, 
    # we guarantee that for any edge u->v (u is parent), v appears after u in the traversal list?
    # In BFS: yes. In DFS: yes (since v is discovered when visiting u).
    
    # Wait, stack pop order. 
    # If stack = [0]. Pop 0. Push 1, 2. Stack = [1, 2] (assuming append adds to end and pop removes from end).
    # Next pop 2. Process 2.
    # Order: 0, 2, ...
    # Is it guaranteed that children come after parents? Yes, because we only add children when visiting parent.
    
    # So iterating `order` in reverse is a valid post-order (bottom-up).
    
    # Initialize sizes to 1 (counting self)
    subtree_size = [1] * n
    
    for u in reversed(order):
        p = parent[u]
        if p != -1:
            subtree_size[p] += subtree_size[u]
            
    return subtree_size
```

Let's double check the constraints and rules.
- "No imports". Checked.
- "Helper functions are allowed".
- "No names beginning with two underscores".
- Builtins list includes `list`, `int`, `len`, `range`, `reversed`.
- `visited` array logic seems sound.

Let's refine the adjacency list construction.
`edges` is a list of lists `[u, v]`.
`adj = [[] for _ in range(n)]` creates a list of empty lists.
Loop over edges: `for edge in edges: u, v = edge[0], edge[1]` ... or just `for u, v in edges:` (unpacking works).

Wait, strict rule: "Only these builtins exist...". Unpacking is language syntax, not a builtin call. It should be fine.
However, to be super safe regarding allowed syntax/builtins, simple indexing might be preferred? No, unpacking `for u, v in edges` is standard Python.
Actually, the prompt says "Only these builtins exist...". It lists specific names. It doesn't ban syntax features like list comprehension or iteration unpacking.

Let's refine the iterative DFS logic to ensure correctness and avoid any hidden recursion depth issues (though 120 is small).
Using a stack for traversal:
```python
    adj = [[] for _ in range(n)]
    for edge in edges:
        u, v = edge[0], edge[1]
        adj[u].append(v)
        adj[v].append(u)
    
    parent = [-1] * n
    order = []
    stack = [0]
    # To avoid re-visiting parent in undirected graph, we need to track visited.
    # Or just check if neighbor != parent. 
    # But parent array is being built. 
    # Easier to keep a visited set or boolean list.
    
    visited = [False] * n
    visited[0] = True
    
    while stack:
        u = stack.pop()
        order.append(u)
        
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                stack.append(v)
    
    subtree_size = [1] * n
    # Iterate in reverse order (leaves to root)
    for i in range(n - 1, -1, -1):
        u = order[i]
        p = parent[u]
        if p != -1:
            subtree_size[p] += subtree_size[u]
            
    return subtree_size
```

Wait, `order` contains vertices. In the loop above, I append `u` after popping.
If stack is `[0]`. Pop 0. `order`=[0]. Neighbors of 0 (say 1) pushed. Stack=`[1]`.
Pop 1. `order`=[0, 1]. Push neighbors...
Yes, this works.

Is `adj[u].append(v)` allowed? Yes, method of list.
Is `range(n - 1, -1, -1)` allowed? Yes.

One edge case: $N=1$. No edges. Loop over edges doesn't run. `adj` has one empty list. `stack`=[0]. Pop 0. `order`=[0]. `parent`=[-1]. Reverse loop runs for `u`=0. `p`=-1. No update. Returns `[1]`. Correct.

Let's check the constraint "data must compare equal to its value before the call".
My code creates new lists (`adj`, `parent`, `order`, `visited`, `subtree_size`). It reads from `data["edges"]` but does not modify it. So `data` remains unchanged.

Wait, $N$ up to 120. Recursion is also totally safe. Maybe recursive solution is shorter and less error-prone?
```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
        
    result = [0] * n
    
    def dfs(u, p):
        s = 1
        for v in adj[u]:
            if v != p:
                s += dfs(v, u)
        result[u] = s
        return s
        
    dfs(0, -1)
    return result
```
Is `def` inside a function allowed? Yes. "The top level may contain only function definitions...". Nested functions are fine.
Recursion depth: 120 is well within default limit (1000).
This is much cleaner.

Are there any restrictions on nested functions?
"Helper functions are allowed."
"No names beginning with two underscores". `dfs` is fine.
Builtins used: `range`, `len` (implicit in loop? No, just iteration), list methods.
Input parsing: `edges` unpacking.

Let's double check the "No imports" rule.
Wait, if I define `dfs` inside `solve`, does it capture `adj` and `result` from closure? Yes.
Is this allowed? Python closures are standard. The constraints list specific *builtins* (functions like `len`, `abs`) that exist in the environment. It doesn't explicitly forbid closures or nested functions, but usually "No imports" and restricted builtins implies a restricted execution environment or just strict coding style. However, since it's an algorithmic task description likely for a platform like Codeforces/LeetCode or a specific grader, standard Python features usually work unless the environment is sandboxed. The prompt says "Only these builtins exist", which might imply a restricted namespace for global lookups?
Actually, looking at the list: `abs, all, any, bool, dict, enumerate, filter, float, int, isinstance, len, list, map, max, min, next, range, reversed, round, set, sorted, str, sum, tuple, zip...`.
It lists specific functions. It doesn't say "Global namespace contains ONLY these". It says "Only these builtins exist", which usually refers to `__builtins__` in a restricted execution context. But `def` and variable assignment are language constructs.

However, sometimes strict environments might block nested functions if they rely on closures for performance or safety? Unlikely for N=120.
But to be absolutely safe and compliant with "Top level may contain only function definitions...", putting logic inside `solve` or defining a helper at top level is safest. Top level helper has access to globals, but we can pass necessary state.

Let's write a non-recursive version just in case, or a helper that takes explicit arguments.
Recursive helper `dfs(u, p, adj, result)` passed as args? Or just define it outside `solve`?
If defined outside `solve`, it needs `adj` and `result`.
But `solve` creates them. So passing them is better.

Let's try the iterative stack approach again to be safe. It avoids recursion depth limits and closure issues (if any).

Refining the Iterative Solution:
1. Parse `n`, `edges`.
2. Build `adj`.
3. BFS/DFS traversal to establish parent pointers and a processing order (post-order).
   - To do post-order iteratively without recursion:
     - One way: Push root to stack. While stack not empty, pop. If node not visited: mark visited, push to `order` list? No.
     - Standard way for post-order size calculation:
       1. Build parent pointers and a list of nodes in topological order (root to leaves).
          - Use a queue or stack for traversal starting at 0.
          - Record `parent[v] = u`.
          - Store nodes in a list `nodes` as they are discovered/visited?
          - Actually, BFS order ensures parents appear before children. Reverse of BFS order ensures children appear before parents.
          - So: BFS from 0 -> get `parent` array and `bfs_order` list.
          - Iterate `bfs_order` in reverse. For each node `u`, add its size to `parent[u]`. Initialize all sizes to 1.
   
   - Wait, BFS order (level order) is fine?
     - Yes. If $v$ is child of $u$, $v$ is added to queue after $u$ is processed. So $v$ comes after $u$ in `bfs_order`.
     - Reverse `bfs_order`: $v$ comes before $u$.
     - When processing $v$, we add its size to parent $u$. Since $u$ hasn't been processed yet in this reverse loop (it appears later in the list, so earlier in reverse), $u$ will accumulate sizes from children.
     - Finally process root (last in original list, first in reverse? No).
     - In reverse loop: first element of `bfs_order` is root (index 0). Last element is deepest leaf.
     - Reverse iteration starts with leaves.
     - Leaf $l$ adds to parent $p$. $p$ is still waiting.
     - Eventually root is processed (it has no parent, or we just ignore adding to non-existent parent).
     - Wait, the loop should add `subtree_size[u]` to `subtree_size[parent[u]]`.
     - If we iterate leaves up:
       - Leaf $l$: size 1. Add to parent $p$.
       - ...
       - Root: size will have accumulated all children. But root has no parent. We don't need to add to anyone.
   
   - Correct logic:
     - `sizes = [1] * n`
     - Traverse to find parents and order.
     - Iterate nodes in reverse topological order (children before parents).
     - For node `u`, if `parent[u]` is not None, `sizes[parent[u]] += sizes[u]`.

   - BFS Implementation details:
     - Queue: list `[0]`.
     - `visited` array or just check parent. Since it's a tree, checking `v != parent[u]` is sufficient if we track parent during traversal. But to avoid backtracking up the edge we came from, we need to know who the parent is.
     - Actually, since it's undirected graph input, when at $u$, neighbors include parent. We must skip parent.
     - In BFS:
       - `queue = [0]`
       - `parent = [-1] * n`
       - `order = []` (to store nodes in visitation order)
       - While queue not empty:
         - `u = queue.pop(0)` (This is O(N) per pop, bad for large N, but N=120 OK. But list.pop(0) is $O(K)$).
         - Better use a pointer index for queue to simulate FIFO with list append.
           - `head = 0`
           - `while head < len(queue): u = queue[head]; head += 1 ...`
     - For each neighbor `v` of `u`:
       - If `v != parent[u]`:
         - `parent[v] = u`
         - `queue.append(v)`
         - `order.append(v)` ? No, we should record visitation order.
         - Actually, `order` list can just be `queue` content?
         - Wait, if we append to `queue`, the queue grows. Iterating with index gives us the nodes in BFS order (0, then children of 0, then grandchildren...).
         - Yes, `queue` will contain `[0, child1, child2, grandchild...]`.
         - This is a valid topological sort for size accumulation?
         - In BFS, parents are visited before children.
         - So if we iterate `queue` from end to start (reverse), we process children before parents.
         - Yes.

   - Wait, checking `v != parent[u]` is tricky because `parent[u]` is set when visiting `u`. But for root, parent is -1.
   - When at root 0: neighbors $v_1, v_2$. `parent[v_1] = 0`, push $v_1$. `parent[v_2] = 0`, push $v_2$.
   - Later pop $v_1$. Neighbors of $v_1$: 0 (parent) and maybe children.
     - Neighbor 0: check `0 != parent[v_1]`? `parent[v_1]` is 0. So skip 0. Correct.
     - Children: `parent` not set (or initialized to -1). We can check if `v` has been visited. But checking `v != parent[u]` works for tree traversal to avoid going back up, *provided* we don't encounter other visited nodes (which shouldn't happen in a tree cycle-free path).
     - Wait, in general graph BFS, we need `visited` array. In tree, checking `v != parent[u]` is sufficient if we are careful?
     - Actually, if we just check `if v != parent[u]`, we might process a node twice if the graph had cycles, but it's a tree.
     - Is it possible to visit a node from a child before setting its parent?
     - In BFS starting at root:
       - Root 0 processed. Neighbors $c_1, c_2$. Set `parent[c_1]=0`, push $c_1$. Set `parent[c_2]=0`, push $c_2$.
       - Next node from queue is $c_1$. Neighbors: 0, maybe $g_1$.
       - Check neighbor 0. Is $0 \neq parent[c_1]$? $0 \neq 0$ is False. Skip. Good.
       - Check neighbor $g_1$. Is $g_1 \neq parent[c_1]$? $g_1 \neq 0$. True.
       - But wait, is `parent[g_1]` set? No.
       - What if there was an edge between $c_1$ and $c_2$? Not a tree (cycle).
       - So in a tree, the only visited neighbor of a node $u$ (other than parent) would be... none, because BFS visits layer by layer. Any other neighbor must be unvisited.
       - Wait, strictly speaking, `v != parent[u]` check is enough to prevent going back up. But do we need to ensure we don't visit a node that was already visited by another path? In a tree, paths are unique. So if `v` is not parent, it must be a child (unvisited).
       - Exception: The root has no parent. If we check `v != parent[0]` (which is -1), neighbors are added.
       - But what if we process $u$, see neighbor $v$. We set `parent[v] = u`. Later, could we encounter $v$ again? No, because it's a tree and we came from parent.
       - Wait, adjacency list is undirected. $u$ has $v$, $v$ has $u$.
       - When processing $u$, we see $v$. We set `parent[v]=u` and push $v$.
       - When processing $v$, we see $u$. We check `u != parent[v]`. `parent[v]` is $u$. So skip.
       - This logic holds.

   - Wait, one detail: Initialization of `parent`.
     - Root 0 has `parent[0] = -1`.
     - Others initialized to something else? Or check if visited?
     - Actually, in the loop `for v in adj[u]:`, if we just rely on `v != parent[u]`, we might re-visit a node if the graph had cycles, but it's a tree. However, for safety and correctness with the `parent` array initialization, maybe explicit visited check is safer?
     - But simpler: In a tree, BFS/DFS order is deterministic.
     - Just use a `visited` boolean array to be safe. It costs little memory.

   - Algorithm Revised:
     1. Build `adj`.
     2. `parent = [-1] * n`, `sizes = [1] * n`.
     3. `order = []` (will store BFS order).
     4. `queue = [0]`
     5. `visited = [False] * n`, `visited[0] = True`
     6. While queue:
          - Pop `u` (using index pointer to keep O(1) or just pop(0) since N=120). Let's use `pop(0)` for simplicity, overhead negligible. Or `queue.pop()` if we don't care about BFS vs DFS order?
          - Wait, if we use stack (`pop()`), it's DFS. Does DFS reverse order work?
            - In DFS, we visit root, go deep to leaf. `order` = [root, ..., leaf].
            - Reverse `order` = [leaf, ..., root].
            - Processing leaf first: add to parent. Parent accumulates.
            - Yes, reverse of any traversal where parent is visited before child works. DFS/BFS both satisfy "parent visited before child" (discovery time).
            - So Stack (DFS) is fine and slightly faster/simpler code (no index management).
     7. Loop with stack:
        - `stack = [0]`
        - `visited = [False]*n`, `visited[0]=True`
        - While stack:
          - `u = stack.pop()`
          - `order.append(u)`
          - For `v` in `adj[u]`:
            - If not `visited[v]`:
              - `visited[v] = True`
              - `parent[v] = u`
              - `stack.append(v)`
     8. Process reverse order:
        - For `u` in `reversed(order)`:
          - `p = parent[u]`
          - If `p != -1`:
            - `sizes[p] += sizes[u]`
     9. Return `sizes`.

   Wait, step 7 logic check:
   Stack LIFO.
   Start `[0]`. Pop 0. Order `[0]`. Push children 1, 2. Stack `[1, 2]`.
   Pop 2. Order `[0, 2]`. Push children of 2...
   Wait, if I push 1 then 2, 2 is popped first.
   Order: 0, 2, ..., 1...
   In this order, parent (0) comes before child (2). Parent (0) comes before child (1).
   So `order` has property: parents appear before children.
   Reverse `order`: children appear before parents.
   Correct.

   One optimization: The `adj` list construction might process edges twice if we iterate all. No, just loop once.
   
   Wait, checking constraints again.
   "edges form a simple undirected tree on 0..n-1".
   Vertices are 0 to n-1.
   Input data keys: "n", "edges".
   
   Data structure of `edges`: `[[u,v], ...]`.
   
   Let's verify logic with an example.
   n=3, edges=[[0,1], [0,2]]. Tree 1-0-2 (star).
   adj: 0:[1,2], 1:[0], 2:[0].
   stack=[0], visited[0]=T.
   Pop 0. order=[0].
   Neighbors 1, 2.
   Visit 1: visited[1]=T, parent[1]=0, stack=[1].
   Visit 2: visited[2]=T, parent[2]=0, stack=[1, 2]. (Assuming append order 1 then 2).
   Pop 2. order=[0, 2].
   Neighbors of 2: [0]. visited[0] is T. Skip.
   Stack=[1].
   Pop 1. order=[0, 2, 1].
   Neighbors of 1: [0]. visited[0] is T. Skip.
   Stack empty.
   
   Reverse order: 1, 2, 0.
   1: parent[1]=0. sizes[0] += sizes[1] (1). sizes=[2, 1, 1].
   2: parent[2]=0. sizes[0] += sizes[2] (1). sizes=[3, 1, 1].
   0: parent[0]=-1. Skip.
   Result [3, 1, 1]. Correct. Subtree at 0 has size 3, at 1 size 1, at 2 size 1.

   Example n=4, edges=[[0,1], [1,2], [2,3]]. Line 0-1-2-3.
   adj: 0:[1], 1:[0,2], 2:[1,3], 3:[2].
   stack=[0]. Pop 0. order=[0]. Push 1. Stack=[1].
   Pop 1. order=[0, 1]. Neighbors 0 (visited), 2 (new). Push 2. Stack=[2].
   Pop 2. order=[0, 1, 2]. Neighbors 1 (vis), 3 (new). Push 3. Stack=[3].
   Pop 3. order=[0, 1, 2, 3]. Neighbors 2 (vis).
   
   Reverse: 3, 2, 1, 0.
   3: p=2. sizes[2]+=sizes[3](1) -> [1,1,2,1].
   2: p=1. sizes[1]+=sizes[2](2) -> [1,3,2,1].
   1: p=0. sizes[0]+=sizes[1](3) -> [4,3,2,1].
   0: p=-1.
   Result [4, 3, 2, 1]. Correct.

   Corner case: n=1, edges=[].
   adj=[[]]. stack=[0]. Pop 0. order=[0].
   Reverse: 0. p=-1. Skip.
   sizes=[1]. Result [1]. Correct.

   Complexity:
   Building adj: O(N) (since tree has N-1 edges).
   DFS traversal: O(N).
   Aggregation: O(N).
   Total O(N). With N=120, extremely fast.

   Code construction details:
   - Need to handle `edges` list correctly.
   - Input `data` is dict.
   
```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    
    # Build adjacency list
    # Using list of lists
    adj = [[] for _ in range(n)]
    for edge in edges:
        u, v = edge[0], edge[1]
        adj[u].append(v)
        adj[v].append(u)
        
    parent = [-1] * n
    visited = [False] * n
    stack = [0]
    visited[0] = True
    
    # We need to store the order of visitation to process bottom-up later
    # Actually, just storing nodes in a list `order`
    order = []
    
    while stack:
        u = stack.pop()
        order.append(u)
        
        # Iterate over neighbors
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                stack.append(v)
                
    # Compute subtree sizes
    # Initialize with 1 (counting self)
    sizes = [1] * n
    
    # Process in reverse order of visitation (children before parents)
    for i in range(len(order) - 1, -1, -1):
        u = order[i]
        p = parent[u]
        if p != -1:
            sizes[p] += sizes[u]
            
    return sizes
```

Wait, `range(len(order) - 1, -1, -1)` is equivalent to `reversed(range(len(order)))`? No, `reversed` on range object is supported in Python 3? Yes. But `range` start/step is allowed. `len` is allowed.
Is `order` guaranteed to have length `n`? Yes, tree is connected.

Let's check the constraints again carefully.
"Only these builtins exist... list, range, len...".
`reversed` is in the list. So `for u in reversed(order):` is cleaner.
Also `edges` unpacking `u, v = edge[0], edge[1]` is safe.

One potential issue: `edges` might be empty?
If `n=1`, `edges=[]`. Loop over edges does nothing. `adj` has 1 empty list. Stack `[0]`. Loop runs once. `order`=[0]. Reverse loop runs once. Returns `[1]`. Correct.

Another check: Vertex indices 0..n-1.
Input guarantees "simple undirected tree on 0..n-1". So vertices are valid.

Is it possible for `data["edges"]` to be missing? The prompt says `data={"n":..., "edges":[...]}`. It seems guaranteed.

One minor thing: `adj[u].append(v)` creates a list of integers. This is fine.
The output must be a list of integers. `sizes` is a list of integers.

Let's refine the code to be strictly within the rules.
No docstrings. No comments? Comments are allowed (they don't break rules). But "The top level may contain only function definitions and names assigned a literal constant... No docstring". This restriction applies to top level. Inside function, comments are fine.

Wait, "No docstring" might apply generally or just top level? "The top level may contain... No docstring". Okay.
But I won't put docstrings anyway to be safe.

Variable names: `adj`, `parent`, `visited`, `stack`, `order`, `sizes`. All standard.
No double underscores.

One logic check: Stack traversal order.
If I use `stack.pop()`, it's DFS.
In DFS, `order` records nodes as they are popped (finished? No, just visited).
Wait, `order.append(u)` happens after popping. This is Pre-order visitation.
Parent is added before children are pushed/popped.
So `order` contains parent before child.
Reverse iteration processes child before parent.
Logic holds.

Let's verify with a small manual trace of stack behavior again.
Tree: 0-1, 0-2.
adj: 0:[1,2], 1:[0], 2:[0].
stack=[0], visited[0]=T.
Pop 0. order=[0].
Neighbors of 0: 1, 2.
Check 1: not visited. visited[1]=T, parent[1]=0, stack.append(1). Stack=[1].
Check 2: not visited. visited[2]=T, parent[2]=0, stack.append(2). Stack=[1, 2].
Pop 2. order=[0, 2].
Neighbors of 2: 0. Visited. Skip.
Stack=[1].
Pop 1. order=[0, 2, 1].
Neighbors of 1: 0. Visited. Skip.
Stack=[].
End.
Order: [0, 2, 1].
Reverse loop:
u=1. parent[1]=0. sizes[0]+=sizes[1] (1). sizes=[2,1,1].
u=2. parent[2]=0. sizes[0]+=sizes[2] (1). sizes=[3,1,1].
u=0. parent[0]=-1. Skip.
Result [3, 1, 1]. Correct.

Wait, stack append order matters for DFS path but not for correctness of "parent before child" in visitation list.
Actually, if I pushed 2 then 1, stack=[2, 1]. Pop 1 first. Order=[0, 1, 2].
Reverse: 2, 1, 0.
2 -> parent 0. sizes[0]+=1.
1 -> parent 0. sizes[0]+=1.
Same result.

What about a deeper tree?
0-1-2.
adj: 0:[1], 1:[0,2], 2:[1].
stack=[0]. Pop 0. order=[0]. Push 1. Stack=[1].
Pop 1. order=[0, 1]. Neighbors 0 (vis), 2 (new). Push 2. Stack=[2].
Pop 2. order=[0, 1, 2]. Neighbor 1 (vis).
Reverse: 2, 1, 0.
2 -> parent 1. sizes[1]+=sizes[2](1) => sizes[1]=2. sizes=[1,2,1].
1 -> parent 0. sizes[0]+=sizes[1](2) => sizes[0]=3. sizes=[3,2,1].
Correct.

Is it possible `order` doesn't contain all nodes?
Only if graph disconnected. But problem says "tree on 0..n-1", which implies connected.

Code looks solid.

One detail: `data["edges"]` contains lists `[u, v]`.
In Python `for edge in edges:` gives `[u, v]`.
`u = edge[0]`, `v = edge[1]` works.
Or `u, v = edge`.

Wait, strict rule check: "Only these builtins exist...".
Is `list` constructor allowed? Yes.
Is `append` method allowed? Yes (method of list).
Is `range` allowed? Yes.
Is `len` allowed? Yes.
Is `int` allowed? Yes.
Is `False`, `True` allowed? They are constants, implicitly available or via `bool`. `bool` is in builtin list. So `bool(0)` -> `False`. But literals `True`/`False` are usually keywords/constants. The prompt says "Names assigned a literal constant...". Wait, it lists allowed types. Usually `True` and `False` are available. If not, `1==1` etc. But standard Python always has them. I will assume standard Python environment where these keywords exist. Actually, looking at the list of builtins, it's quite specific. It doesn't list `True` or `False`. However, `bool` is there. So maybe `bool(0)` is needed? No, that's pedantic. Usually "builtins" refers to functions/objects in `__builtins__`. Keywords are language syntax. I will use `True` and `False` as they are fundamental.

Actually, to be extremely safe, I can initialize `visited` with `[0] * n` (integers) and check `if visited[v] == 0:`. But `False` is safer/cleaner.
Wait, "The top level may contain only function definitions and names assigned a literal constant".
This implies I cannot have `VISITED = False` at top level. But inside `solve`, variable assignment is fine.
And literals like `True` are expressions.

Let's check if there's any tricky constraint about "normalized JSON types".
"Results are graded after JSON serialization and parsing... Use Python int (not bool) for integer results".
My result `sizes` contains integers.
List of integers. Matches schema.

One final check on input reading.
`data` is a dict.
`n = data["n"]`.
If `n` is not in `data`, KeyError. But problem says valid input.

What if `edges` is empty and `n > 1`? Impossible for tree (needs n-1 edges). But code would handle it (disconnected components, sizes would be 1 for component containing 0, others 1? Wait, other nodes wouldn't be visited, so parent stays -1. Loop `reversed(order)` would only process node 0. Sizes for other nodes remain 1. But they are not in tree rooted at 0? "Tree on 0..n-1" implies connected. So we don't need to worry.)

Wait, if `n` is large (120), recursion limit is not an issue.
But I used iterative solution anyway.

One optimization: The adjacency list construction iterates edges.
Input edges are `[u, v]`.
We do `adj[u].append(v)` and `adj[v].append(u)`.
If `n` is 120, this is very fast.

Let's write the final code block.

```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    
    # Build adjacency list for the tree
    adj = [[] for _ in range(n)]
    for edge in edges:
        u = edge[0]
        v = edge[1]
        adj[u].append(v)
        adj[v].append(u)
        
    # Iterative DFS to determine parent pointers and processing order
    # Stack for traversal
    stack = [0]
    
    # Track visited nodes to avoid cycles/back-tracking (though tree has no cycles, undirected edges go back to parent)
    # Using a list of booleans. 
    # Since 'bool' is not in the explicit builtin list, but True/False are standard constants. 
    # If strict, use integers 0/1. Let's use integers for max compatibility with restricted environments?
    # "Only these builtins exist: ... bool ...". It lists bool. So bool(0) works. 
    # But literals True/False are likely fine. I'll stick to standard Python.
    # Actually, let's use a set or integer array to be safe against any weird restrictions on boolean literals?
    # No, Python is standard.
    
    visited = [False] * n
    visited[0] = True
    
    parent = [-1] * n
    order = []
    
    while stack:
        u = stack.pop()
        order.append(u)
        
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                stack.append(v)
                
    # Calculate subtree sizes
    # Initialize size of each node to 1 (counting itself)
    sizes = [1] * n
    
    # Iterate in reverse order of visitation (children before parents)
    for i in range(len(order) - 1, -1, -1):
        u = order[i]
        p = parent[u]
        if p != -1:
            sizes[p] += sizes[u]
            
    return sizes
```

Wait, `range` is a builtin. `len` is a builtin.
In Python 3 `range` returns an object. `range(start, stop, step)` works.
Wait, `range(len(order) - 1, -1, -1)`:
If `order` has length $L$. Indices $0 \dots L-1$.
Start $L-1$. Stop $-1$ (exclusive). Step $-1$.
Generates $L-1, L-2, \dots, 0$. Correct.

Double check: "No imports". `import` keyword not used.
"No classes". None used.
"No decorators". None used.
"Function default values must be literals". No defaults used.
"Helper functions allowed". I put everything in `solve`.
"Top level may contain only function definitions...". Code is just `def solve...`.

One detail: `data` dict keys are strings "n", "edges".
My code uses string keys. Correct.

Wait, looking at the rules again:
"The top level may contain only function definitions and names assigned a literal constant... No docstring, if __name__ guard or other top-level statement."
This is satisfied.

What about `visited` array initialization? `[False] * n`.
Is `False` a literal constant? Yes.
Is `*` operator allowed on lists? Yes.

Is there any restriction on using list multiplication? No.

Wait, the prompt says "Use Python int (not bool) for integer results".
My result is list of ints.
But intermediate `visited` array uses booleans. That's fine, it's not the return value.

One paranoid check:
Is `data["n"]` guaranteed to be integer? Yes.
Is `edges` list of lists of ints? Yes.

Alternative for `visited`: Use a set?
`visited = set()`, `visited.add(0)`.
Check `if v not in visited`.
Set operations are allowed (methods of built-in types).
But array lookup is faster and simpler. Given N=120, irrelevant.
Array is fine.

Let's do a quick check on "data must compare equal to its value before the call".
My code reads `data` but never writes to it.
It creates new lists.
So `data` is untouched.

One edge case: `n=0`?
Prompt says `n` integer 1..120. So `n >= 1`.
Vertices 0..n-1. So at least vertex 0.

Code looks good.

```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    
    # Build adjacency list
    adj = [[] for _ in range(n)]
    for edge in edges:
        u, v = edge[0], edge[1]
        adj[u].append(v)
        adj[v].append(u)
        
    # Iterative DFS to establish parent pointers and traversal order
    stack = [0]
    visited = [False] * n
    visited[0] = True
    
    parent = [-1] * n
    order = []
    
    while stack:
        u = stack.pop()
        order.append(u)
        
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                stack.append(v)
                
    # Compute subtree sizes bottom-up
    sizes = [1] * n
    
    # Reverse order ensures children are processed before parents
    for i in range(len(order) - 1, -1, -1):
        u = order[i]
        p = parent[u]
        if p != -1:
            sizes[p] += sizes[u]
            
    return sizes
```
Wait, unpacking `u, v = edge[0], edge[1]` or just `u, v = edge`?
`edge` is `[u, v]`. `u, v = edge` works.
But to be explicit and safe against any weird type issues (though input is guaranteed), `edge[0]` is fine.
Actually `u, v = edge` is cleaner. I'll use that or indexing. Indexing is safer if edge has more items? No, simple tree edges are pairs.
I used `u, v = edge[0], edge[1]` in thought process, which is robust.

Wait, `edge` is a list `[u, v]`. `u = edge[0]`, `v = edge[1]`.
Is `edge` guaranteed to be a list? `edges` is a list of edges. Edges are `[u,v]`. Yes.

Final check on "results graded after JSON serialization".
Python `True`/`False` serialize to `true`/`false`.
Integers serialize to numbers.
List serializes to array.
If I returned a boolean somewhere where integer expected, it would be type mismatch in JSON?
JSON doesn't distinguish int/float (usually), but strict typing might.
But `sizes` are definitely ints.

One check: "Use Python int ... for integer results".
My list contains `1` (int) and sums of ints (int). Correct.

The solution seems complete.

One tiny thing: The problem says "edges form a simple undirected tree on 0..n-1".
If n=1, edges=[]. adj=[[ ]]. stack=[0]. loop runs. order=[0]. sizes=[1]. returns [1].
If n=2, edges=[[0,1]]. adj=[[1], [0]]. stack=[0]. pop 0. order=[0]. push 1. pop 1. order=[0, 1]. parent[1]=0. sizes init [1, 1]. reverse loop: u=1, p=0 -> sizes[0]+=1 => [2, 1]. u=0, p=-1. returns [2, 1]. Correct.

Wait, stack order with neighbors.
If adj[0] = [1].
stack=[0]. pop 0. order=[0]. loop v in [1]. visited[1]=F. set T. parent[1]=0. stack=[1].
Next iter: pop 1. order=[0, 1]. neighbors [0]. visited[0] is T. skip.
Order [0, 1]. Reverse 1, 0.
Correct.

What if adj[0] = [2, 1]? (Neighbor 2 first).
stack=[0]. pop 0. order=[0].
v=2: push 2. stack=[2].
v=1: push 1. stack=[2, 1].
pop 1. order=[0, 1]. ... (process subtree of 1)
... push 1's children? None.
pop 2. order=[0, 1, 2]. (Wait, 2 was popped after 1).
Order: 0, 1, 2.
Reverse: 2, 1, 0.
Processing 2: parent 0. sizes[0]+=sizes[2].
Processing 1: parent 0. sizes[0]+=sizes[1].
Order of adding doesn't matter for sum.
Result correct.

Wait, stack is LIFO.
If I push 2 then 1. Stack top is 1. Pop 1 first.
So DFS explores 1's branch fully before 2?
Yes.
But regardless, 0 is always popped first (root).
Children of 0 are pushed. They will be popped later.
So parent (0) is always added to `order` before children (1, 2).
Because to push a child, we must pop the parent first.
Wait.
Pop parent -> add to order -> push children.
So Parent is in `order` before Children are pushed.
Children are popped later and added to `order`.
So yes, Parent index < Child index in `order`.
So `order` is topological sort (parents before children).
Reverse is post-order (children before parents).
Logic holds.

Final check on imports. None used.
Code is self-contained.

```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    
    # Build adjacency list
    adj = [[] for _ in range(n)]
    for edge in edges:
        u = edge[0]
        v = edge[1]
        adj[u].append(v)
        adj[v].append(u)
        
    # Iterative DFS to traverse the tree and record order
    stack = [0]
    visited = [False] * n
    visited[0] = True
    
    parent = [-1] * n
    order = []
    
    while stack:
        u = stack.pop()
        order.append(u)
        
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                stack.append(v)
                
    # Compute subtree sizes bottom-up
    # Initialize sizes to 1 (counting the node itself)
    sizes = [1] * n
    
    # Iterate in reverse visitation order (children before parents)
    for i in range(len(order) - 1, -1, -1):
        u = order[i]
        p = parent[u]
        if p != -1:
            sizes[p] += sizes[u]
            
    return sizes
```

Wait, `range` with negative stop. `range(start, stop, step)`.
If `len(order)` is 0? `n>=1` so len>=1.
If `len` is 1. `range(0, -1, -1)`. Yields 0. Correct.

One syntax detail: `adj[u].append(v)`. `u` is int. `v` is int.
List of lists works.

Is there any case where `edge` might be tuple? "edges:[[u,v],...]". List of lists. Even if tuple, indexing works.

Final verification of the constraints on variable names.
No `_` prefix names.
My vars: `n`, `edges`, `adj`, `u`, `v`, `stack`, `visited`, `parent`, `order`, `sizes`, `i`, `p`.
All safe.

One paranoid check:
Is it possible `data["edges"]` contains integers directly? No, "edges:[[u,v],...]".
Is it possible `n` is not the first key? Dict order doesn't matter for lookup.

Ready.


## Entire final response

```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    
    # Build adjacency list
    adj = [[] for _ in range(n)]
    for edge in edges:
        u = edge[0]
        v = edge[1]
        adj[u].append(v)
        adj[v].append(u)
        
    # Iterative DFS to traverse the tree and record order
    stack = [0]
    visited = [False] * n
    visited[0] = True
    
    parent = [-1] * n
    order = []
    
    while stack:
        u = stack.pop()
        order.append(u)
        
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                stack.append(v)
                
    # Compute subtree sizes bottom-up
    # Initialize sizes to 1 (counting the node itself)
    sizes = [1] * n
    
    # Iterate in reverse visitation order (children before parents)
    for i in range(len(order) - 1, -1, -1):
        u = order[i]
        p = parent[u]
        if p != -1:
            sizes[p] += sizes[u]
            
    return sizes
```
