# CORRECT

Question: HV3-DEPENDENCY_DAG-04 | Quantization: Q8_0 | Status: correct

Solution correct: True | Strict response correct: False

Hidden tests passed: 51/51 | First failure (index only): null

Inference seconds: 503.47352223100006 | Decode tokens/s: 33.658572555175475 | Thinking budget exhausted: None | Output cap reached: False

## Exact prompt

Algorithmic Python task. data={"n":integer 0..50,"edges":[[u,v],...]}; labels 0..n-1, no self-loops or duplicate edges, at most 150 edges. Cycles are allowed in the input. Each edge u->v means u must come before v.

Return a list whose entry v is the number of distinct other vertices having a directed path to v. Return [] if a cycle exists; n=0 returns [].
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

The problem asks us to compute, for each vertex $v$ in a directed graph, the number of distinct vertices that have a directed path to $v$. If there is a cycle in the graph, we should return an empty list `[]`. If $n=0$, we should return `[]`. The input graph is given as a dictionary with keys "n" (number of vertices) and "edges" (list of directed edges). The vertices are labeled 0 to $n-1$.

    *   Input: `data` dictionary.
    *   Output: List of integers, or `[]` if cycle exists.
    *   Constraints: $n \le 50$, number of edges $\le 150$. No self-loops, no duplicate edges. Cycles possible (but handled). Time limit is generous for these constraints ($O(n^3)$ or even $O(n^4)$ is fine).

    If the graph contains a cycle, return `[]`.
    Otherwise, compute the transitive closure or, more specifically, for each node $v$, count the size of the set $\{u \mid u \leadsto v\}$. Note that "path to $v$" usually implies length $\ge 1$ (other vertices), so we exclude $v$ itself. The prompt says "number of distinct other vertices having a directed path to v".

    Since $n$ is small ($n \le 50$), Floyd-Warshall algorithm or running BFS/DFS from each node or reversing edges and searching is feasible.
    
    Let's check the cycle detection requirement. If there is a cycle, *any* vertex in the cycle (and vertices reachable from the cycle) would technically be reachable from the cycle. However, the problem statement simply says "Return [] if a cycle exists". It doesn't distinguish between cycles and non-cycles, just existence of *any* cycle in the graph.

    1.  Parse $n$ and edges.
    2.  Build adjacency list or matrix.
    3.  Detect if there is a cycle.
        *   Since it's a directed graph, we can use DFS with coloring (white/gray/black) or Kahn's algorithm (topological sort).
        *   If cycle detected -> return `[]`.
    4.  If no cycle (DAG), compute reachability.
        *   We need to count incoming paths for each node.
        *   Since edges are directed $u \to v$, a path $x \to y$ means $y$ is reachable from $x$. We want for each $v$, count of $u$ such that there is a path $u \to v$.
        *   This is equivalent to finding the number of ancestors for each node in the DAG.
    5.  Algorithm choice:
        *   **Approach 1: Floyd-Warshall.** Compute transitive closure matrix `reach[i][j]` which is true if path $i \to j$ exists. Then for each column $j$, count trues. Also, check for cycle: if `reach[i][i]` is true for any $i$, there's a cycle. Note: Floyd-Warshall with initialization `reach[i][j] = 1` if edge $i \to j$ else 0, and `reach[i][i] = 0` initially (since no self loops allowed by input spec, though path of length 0 isn't usually counted as "other vertices"). Wait, standard FW detects cycles if diagonal becomes true.
        *   **Approach 2: Reverse Graph BFS/DFS.** To find who reaches $v$, we can look at the graph where edges are reversed ($v \to u$). Then from $v$, traverse backwards to find all $u$. Count them. Check for cycle separately or during this? Cycle detection is needed globally.
        *   **Approach 3: Topological Sort + DP.** If no cycle, we can do a topological sort. Process nodes in topo order. For each node $u$, it contributes to the set of ancestors of its neighbors $v$. But we need to merge sets of ancestors. With $n=50$, bitsets (using integers) or sets are fine.
            *   Ancestors($v$) = $\bigcup_{(u, v) \in E} (\text{Ancestors}(u) \cup \{u\})$.
            *   Wait, if $u \to v$, then all ancestors of $u$ are ancestors of $v$, plus $u$ itself.
    
    Let's refine Approach 3 (DAG DP).
    1. Build adjacency list `adj` for forward graph ($u \to [v_1, v_2...]$) and reverse graph `rev_adj` ($v \to [u_1, u_2...]$)? Or just use topological sort order.
    2. Compute in-degrees to run Kahn's algorithm.
       - Queue $Q$ with all nodes having in-degree 0.
       - List `order` to store topo order.
       - While $Q$ not empty: pop $u$, add to `order`, decrement in-degree of neighbors. If neighbor in-degree becomes 0, push to $Q$.
       - If `len(order) < n`, there is a cycle -> return `[]`.
    3. Compute ancestor counts.
       - Let `ancestors[v]` be the set of vertices having a path to $v$.
       - Process nodes in topological order. For each node $u$ (which appears before all its descendants), we can update its children?
       - Actually, if we process in topological order, when we are at $u$, we know the full set of ancestors for $u$. We can propagate this to neighbors $v$ such that $u \to v$.
       - `ancestors[v] |= ancestors[u] | {u}`.
       - But wait, a node $v$ might have multiple incoming edges from $u_1, u_2$. We need to aggregate.
       - Since it's a DAG, processing in topological order ensures that when we process an edge $u \to v$, we might not have processed $v$ yet (if $v$ is after $u$), or if we are iterating over edges.
       - Better: Initialize `ancestors` sets for all nodes as empty.
       - Iterate $u$ in topological order.
         - For each neighbor $v$ of $u$ (edge $u \to v$):
           - `ancestors[v] = ancestors[v] | ancestors[u] | {u}`.
         - Wait, this logic is slightly flawed because we might update `ancestors[v]` multiple times from different parents, but sets handle unions. The issue is that when we are at $u$, `ancestors[u]` must be fully computed. In a topological sort, all predecessors of $u$ appear before $u$. So yes, `ancestors[u]` is ready.
         - However, simply iterating edges $u \to v$ in topo order works if we are careful.
         - Let's trace: Topo order $v_1, v_2, \dots, v_n$.
         - When at $v_i$, `ancestors[v_i]` should be the union of ancestors of all parents + parents themselves. But parents appear earlier in topo order.
         - Actually, we can just propagate forward.
         - For each $u$ in topo order:
           - `ancestors[u]` is already fully computed (since all incoming edges come from nodes processed earlier). Wait, no. The sets accumulate. If we initialize all sets empty, and when processing $u$, we push its set to children?
           - Correct logic:
             1. Compute topo order. If cycle, return [].
             2. Initialize `sets = [set() for _ in range(n)]`.
             3. For $u$ in topo_order:
                - The set of ancestors for $u$ is ready? Not quite. We need to pull from parents or push to children.
                - If we push: When processing $u$, `sets[u]` contains all nodes reaching $u$. Add `u` to all `sets[v]` where $u \to v$. Also add everything in `sets[u]` to `sets[v]`.
                - This is $O(n^3)$ or $O(n^2 + E \cdot n)$. With $n=50$, very fast.
    
    Wait, "number of distinct other vertices". So for node $v$, result is `len(ancestors[v])`. The set should not include $v$ itself?
    - Path to $v$ excludes $v$ (other vertices).
    - In the propagation logic: `sets[u]` stores ancestors of $u$. It does not contain $u$.
    - When moving from $u$ to $v$ ($u \to v$), $u$ becomes an ancestor of $v$. And all ancestors of $u$ become ancestors of $v$.
    - So update: `sets[v].update(sets[u]); sets[v].add(u)`.
    - Since we process in topo order, when we are at $u$, `sets[u]` is fully populated?
      - Let's check. $u$ might have parents $p_1, p_2$. Both $p_1, p_2$ appear before $u$ in topo order. So they would have pushed their information to $u$ already. Yes.
    - However, we need to make sure we iterate through the graph structure correctly. Just iterating topological order and for each node pushing to neighbors is sufficient.

    Example: $1 \to 2$. Topo: 1, 2.
    - Init `sets = [{}, {}]`.
    - Process 1: Neighbors [2]. Update `sets[2]` with `{}` and add `1`. `sets[2]` becomes `{1}`.
    - Process 2: Neighbors []. Done.
    - Result for 2 is `len({1})` = 1. Correct.

    Example: $1 \to 3, 2 \to 3$. Topo: 1, 2, 3 (or 2, 1, 3).
    - Init `sets = [{}, {}, {}]`.
    - Process 1: Push to 3. `sets[3]` gets `{}` and adds `1` -> `{1}`.
    - Process 2: Push to 3. `sets[3]` gets `{}` (from 2's empty ancestors) and adds `2`. Union with existing?
      - Ah, the update must be a union. `sets[3].update(sets[2])` then `sets[3].add(2)`.
      - `sets[3]` was `{1}`. Update with `{}` -> still `{1}`. Add `2` -> `{1, 2}`.
    - Process 3: No neighbors.
    - Result for 3 is 2. Correct.

    Is it guaranteed that by the time we process $u$, all its parents have finished pushing?
    Yes, because topological order guarantees parents appear before children. Wait, in Kahn's algo or DFS based topo sort, if there is an edge $p \to u$, $p$ comes before $u$.
    Wait, standard Kahn's algorithm produces a sequence where for every edge $(u, v)$, $u$ comes before $v$.
    So when we are at $u$ in the loop, any parent $p$ of $u$ has already been processed and has pushed its data to $u$.
    Wait, if $p \to u$, $p$ is processed before $u$. $p$ pushes to neighbors. One neighbor is $u$. So $u$ receives updates from $p$ while $p$ is being processed. Since $p$ comes before $u$, the update happens before we reach $u$ in the loop?
    No, the update happens *during* the processing of $p$. The variable `sets[u]` is modified. When the loop reaches $u$, it reads the accumulated state of `sets[u]`. Since all parents are processed before $u$, all pushes to $u$ are done.
    Correct.

    Cycle detection with Kahn's:
    - Count in-degrees.
    - Queue = nodes with in-degree 0.
    - While queue not empty: pop, add to order, decrement neighbors' in-degree, if 0 push.
    - If `len(order) != n`, cycle exists.

    Wait, there is a subtle point.
    In Kahn's algo, we modify the graph (decrement degrees). We need to keep original graph for processing or just store adjacency list separately. Adjacency list is fine.

    Wait, checking constraints. $n \le 50$.
    Complexity:
    - Topo sort: $O(V+E)$.
    - Propagation: For each edge $(u, v)$, we do set union and add. Set size $\le n$. Cost per edge $O(n)$. Total $O(E \cdot n)$.
    - $50 \times 150 \times 50$ operations roughly? Actually set union is proportional to size. Max size 50. $150 \times 50 = 7500$ ops. Extremely fast.

    Wait, "edges" list might contain duplicate edges? Problem statement says "no self-loops or duplicate edges". So adjacency list is clean.

    One edge case: $n=0$.
    Input `data={"n": 0, "edges": []}`.
    Output `[]`.
    The logic: topo order loop range(0) -> empty. Order length 0 == n.
    Result array of size 0. Returns `[]`.
    Wait, if $n=0$, result should be `[]`? "n=0 returns []". Yes.

    What if graph is disconnected? Works fine.
    What if cycle exists? Kahn's detects it.

    Let's refine the Kahn's implementation details.
    
    1. Parse `n = data["n"]`, `edges = data["edges"]`.
    2. If $n=0$, return `[]`. (Wait, checking spec "Return [] if a cycle exists; n=0 returns [].").
       Actually, if $n=0$, loop won't run, result list empty?
       Let's verify. The problem asks for "list whose entry v is...". If no vertices, empty list.
    3. Build adjacency list `adj` (for graph traversal) and compute in-degrees `in_degree`.
       - `adj = [[] for _ in range(n)]`
       - `in_degree = [0] * n`
       - For $u, v$ in edges: `adj[u].append(v)`, `in_degree[v] += 1`.
    4. Queue initialization: collect all $i$ where `in_degree[i] == 0`.
    5. Topo sort list `order = []`.
    6. While queue:
       - pop $u$.
       - append to `order`.
       - for $v$ in `adj[u]`:
         - `in_degree[v] -= 1`
         - if `in_degree[v] == 0`: push $v$.
    7. If `len(order) < n`: return `[]`.
    8. Initialize `ancestors = [set() for _ in range(n)]`.
    9. Iterate $u$ in `order`:
       - We need to push data to neighbors?
       - Wait, if we iterate $u$ in `order`, and for each neighbor $v$, we update `ancestors[v]`.
       - But `ancestors[u]` must be ready.
       - Is `ancestors[u]` ready when we reach $u$?
       - Yes, because all parents of $u$ are processed before $u$. They updated `ancestors[u]`.
       - However, we need to be careful with the order of operations.
       - When we process parent $p$, we update child $c$'s set.
       - So when loop reaches $c$, `ancestors[c]` has received updates from all parents (since all parents are before $c$).
       - Then when processing $c$, we push its accumulated set to its children.
       - This works.

    Wait, check the "push" logic again.
    When processing $u$:
      For each $v$ in `adj[u]`:
        `ancestors[v].update(ancestors[u])`
        `ancestors[v].add(u)`
    
    Is this correct?
    Path to $v$ comes from parents.
    If $u \to v$, then $u$ is an ancestor of $v$. And all ancestors of $u$ are ancestors of $v$.
    So yes, we take `ancestors[u]`, add `u` to it, and union with `ancestors[v]`.
    
    Wait, order of updating.
    If multiple parents update the same child $v$, does it matter? No, set union is commutative/associative.
    Does the order of processing nodes in topological sort matter for correctness?
    Topological sort ensures parents processed before children.
    Wait, if we process $u$, we modify `ancestors` of its children.
    Suppose $u \to v$ and $w \to v$. Both $u, w$ are parents of $v$.
    In topo order, both $u$ and $w$ must appear before $v$.
    When loop processes $u$, it updates `ancestors[v]`.
    When loop processes $w$, it updates `ancestors[v]`.
    Finally, loop reaches $v$. At this point, `ancestors[v]` has accumulated info from all parents.
    Then loop processes $v$ and pushes to its children.
    This is correct.

    Wait, what if there are multiple edges? (Not allowed per spec).
    
    Optimization: Instead of sets, use integers as bitmasks?
    $n \le 50$. Python handles large integers automatically. Bitmask operations are faster than set operations?
    Maybe simpler to implement with sets given small $N$. Sets are robust.
    However, integer bitmask is very concise.
    `ancestors[u]` as integer where bit $k$ is 1 if $k \in$ ancestors.
    Update: `ancestors[v] |= (ancestors[u] | (1 << u))`.
    Wait, `(1 << u)` sets the bit for $u$. `ancestors[u]` is mask of ancestors of $u$.
    So new bits to add are `ancestors[u] | (1 << u)`.
    Actually `1 << u` represents the node $u$ itself.
    Wait, if we use bitmask, index 0 corresponds to bit 0? Yes.
    
    Let's check constraints again. $n \le 50$.
    Bitmask fits in standard integer (Python ints are arbitrary precision).
    Operations are fast.
    Counting bits: `bin(mask).count('1')` or similar.
    
    Wait, "distinct other vertices". So for vertex $v$, we count bits in `ancestors[v]`. Note that `ancestors[v]` should not include bit $v$.
    In the update logic: `ancestors[v] |= ancestors[u] | (1 << u)`.
    Since $u \neq v$ (no self loops), and $u$ is not in `ancestors[u]` (by invariant), adding $u$ doesn't conflict with existing bits of $v$ unless $u=v$, which is impossible.
    Wait, could $u$ be already in `ancestors[v]`?
    If there's a cycle, yes. But we detect cycles and return [].
    If DAG, no path from $v$ to $u$ if edge is $u \to v$. So $u$ is not in `ancestors[v]` initially.
    Wait, transitive closure might add paths? No, we are building it.
    In a DAG, ancestors of $v$ are strictly "upstream". $u$ is immediate upstream. It cannot be downstream.
    So bit $u$ will not be set in `ancestors[v]` before this update.
    
    Wait, what if there are multiple paths? Union handles it.
    
    Let's refine bitmask approach.
    1. `adj`, `in_degree`.
    2. Topo sort. If fail -> `[]`.
    3. `masks = [0] * n`. (Integer masks).
    4. For $u$ in topo_order:
         - current_mask = `masks[u]`
         - # We want to propagate this to neighbors.
         - # But wait, `masks[u]` currently holds ancestors of $u$.
         - # The set of nodes reaching neighbors $v$ via $u$ is `current_mask | (1 << u)`.
         - push_mask = `current_mask | (1 << u)`
         - For $v$ in `adj[u]`:
             - `masks[v] |= push_mask`
    5. Result: `[bin(m).count('1') for m in masks]`?
       Wait, `bin()` returns string like '0b...'. count('1') works.
       Or just a loop to count bits? Or `int.bit_count()` available in Python 3.10+.
       Is `bit_count` allowed? It's a method of int. The constraints list allowed builtins, but methods of built-ins are allowed. "Methods of built-in types (list, dict, str, int, ...) may be used." So `int.bit_count()` should be fine. But to be safe and compatible with older Python 3 versions (like 3.8 used in some judges), `bin(x).count('1')` is safer or manual loop. Given "Python task", usually latest stable. But `bin().count()` is very safe.
    
    Wait, `masks[v] |= push_mask`.
    Does this preserve the property that `masks[u]` only contains strict ancestors?
    When we process $u$, `masks[u]` has been updated by all its parents.
    Since parents are processed before $u$ (in topo order), yes.
    However, there's a potential issue with the loop structure.
    We iterate $u$ in topo order.
    When we are at $u$, we read `masks[u]`.
    Is it possible that `masks[u]` is updated *after* we read it?
    No, because updates to `masks[u]` come from parents $p$. $p$ must appear before $u$ in topo order. So $p$'s loop iteration happens before $u$'s loop iteration. $p$ writes to `masks[u]`.
    So when we reach $u$, `masks[u]` is final.
    
    Wait, what if the graph has no edges?
    Topo order: 0, 1, ..., n-1.
    Loop $u=0$: neighbors empty.
    ...
    All masks 0. Result all 0. Correct.
    
    What if cycle?
    Topo sort fails (order length < n). Return `[]`. Correct.

    Wait, check the "Return [] if a cycle exists" logic again.
    If cycle exists, Kahn's algorithm will not process all nodes.
    Specifically, nodes in the cycle and nodes reachable only from the cycle will never have in-degree 0 (or become 0).
    So `len(order)` will be $< n$.
    We return `[]`.
    
    One detail: The problem says "Return [] if a cycle exists".
    Is it possible that a graph has a cycle but also nodes not reachable from the cycle?
    Yes. But the requirement is simply "if a cycle exists [in the input graph], return []". It doesn't ask to compute anything. Just check existence of *any* cycle.
    Kahn's algorithm detects if the whole graph is a DAG. If it detects a cycle (by failing to process all nodes), we return `[]`.
    Wait, does Kahn's detect cycles in disconnected components?
    Yes. It processes all nodes with in-degree 0. If there's a cycle somewhere, those nodes won't be processed. So total processed count < n.
    
    Wait, "Return [] if a cycle exists; n=0 returns []."
    Wait, if $n=0$, loop range(0) is empty, order is [], len(order)=0=n. Logic proceeds?
    Step 4: `masks` initialized.
    Step 5: loop over empty order -> nothing happens.
    Step 6: result `[bin(0).count('1') for ...]` -> `[0] * 0` -> `[]`.
    Wait, if $n=0$, we return `[]`.
    The code should handle $n=0$ naturally?
    If $n=0$, edges list empty.
    Topo sort: queue empty. order empty. len(order)=0=n.
    masks array size 0.
    result list comprehension over range(0) -> [].
    Seems correct.
    
    But wait, problem statement says "n=0 returns []".
    If $n > 0$ and no cycles, result is list of length $n$.
    Wait, for $n=0$, result is empty list.
    The logic holds.

    Let's double check the constraints and rules.
    - No imports.
    - `solve(data)` function.
    - Input format: `data` dict.
    - Output: JSON serializable list of ints.
    
    Potential pitfall:
    Bitmask size. $n=50$. `1 << 49` is huge but fine for Python.
    Time complexity: $O(N^2 + E)$ roughly? Topo sort $O(V+E)$. Loop runs $V$ times, inner loop over edges. Set operations (bitwise OR) on integers of size $N$ bits takes $O(N/word\_size)$ or effectively $O(1)$ for small $N$, but mathematically linear in bits. So $O(E \cdot N / 64)$. With $N=50$, very fast.
    
    Space complexity: $O(V + E)$ for adj, $O(N^2/8)$ for masks? Or just $O(N)$ integers of size $N$ bits. Fine.

    Let's dry run a cycle case.
    Edges: `[[0, 1], [1, 0]]`. $n=2$.
    Adj: `0:[1]`, `1:[0]`.
    In-degrees: `0:1`, `1:1`.
    Queue: empty (no 0 in-degree).
    Loop while queue: doesn't run.
    Order: [].
    Len(order) = 0 != 2.
    Return `[]`. Correct.

    Another cycle case: $0 \to 1$, $1 \to 2$, $2 \to 0$.
    In-degrees all 1. Queue empty. Order empty. Fail. Return `[]`.

    Disconnected cycle: $0 \leftrightarrow 1$, $2$ isolated.
    In-degrees: `0:1, 1:1, 2:0`.
    Queue: `[2]`.
    Pop 2. Order `[2]`. Neighbors of 2: none.
    Queue empty.
    Order len 1 != 3. Return `[]`. Correct.

    What if input edges are not sorted or have duplicates?
    Spec says "no self-loops or duplicate edges". So we can assume valid input regarding that. But good to be safe?
    Spec: "labels 0..n-1, no self-loops or duplicate edges". We rely on this.
    
    Is it possible for `edges` to be empty but $n > 0$? Yes.
    Graph with isolated vertices. No cycles.
    In-degrees all 0. Queue `[0..n-1]`.
    Order `[0..n-1]`.
    Loop $u=0$: neighbors empty. masks[0]=0. Push nothing.
    ...
    Result: `[0, 0, ..., 0]`. Correct.

    What if graph is a line $0 \to 1 \to 2$.
    Edges `[[0,1], [1,2]]`. $n=3$.
    In-degrees: `0:0, 1:1, 2:1`.
    Queue `[0]`.
    Pop 0. Order `[0]`. Neighbors `[1]`. Decr in-degree[1] to 0. Push 1.
    Pop 1. Order `[0, 1]`. Neighbors `[2]`. Decr in-degree[2] to 0. Push 2.
    Pop 2. Order `[0, 1, 2]`. Neighbors `[]`.
    Len 3 == 3. OK.
    Masks init `[0, 0, 0]`.
    Process 0: `push_mask` = `masks[0] | (1<<0)` = `0 | 1` = `1` (binary 1).
       Neighbors of 0: `[1]`.
       `masks[1] |= 1` -> `1`.
    Process 1: `masks[1]` is `1`.
       `push_mask` = `1 | (1<<1)` = `1 | 2` = `3` (binary 11).
       Neighbors of 1: `[2]`.
       `masks[2] |= 3` -> `3` (binary 011).
    Process 2: `masks[2]` is `3`.
       `push_mask` = `3 | (1<<2)` = `3 | 4` = `7` (111).
       Neighbors `[]`.
    Result bits count:
    masks[0]=0 -> 0.
    masks[1]=1 -> 1 (ancestor 0). Correct.
    masks[2]=3 -> 2 (ancestors 0, 1). Correct.

    Wait, check mask logic for $u=0$.
    `masks[0]` is 0.
    We want to add 0 as ancestor of 1.
    So neighbor 1 should have bit 0 set.
    `push_mask` calculation: `masks[u] | (1 << u)`.
    `0 | 1` = 1. Correct.
    
    Check $u=1$.
    `masks[1]` is 1 (bit 0 set). Represents ancestor 0.
    We want to propagate ancestors of 1 (which are {0}) plus 1 itself, to neighbors of 1.
    Neighbors of 1: {2}.
    Ancestors of 2 should include {0, 1}.
    `push_mask` = `masks[1] | (1 << 1)` = `1 | 2` = 3 (bits 0 and 1).
    Update `masks[2] |= 3`.
    `masks[2]` becomes 3. Bits 0 and 1 set.
    Count = 2. Correct.

    Looks solid.

    Wait, one detail: The problem says "Return a list whose entry v is the number of distinct other vertices having a directed path to v."
    If there is a cycle, return `[]`.
    My code returns `[]` if cycle detected.
    
    What about $n=0$?
    Code produces `[]`. Correct.

    One check: "distinct other vertices".
    Does the mask include $v$ itself?
    In my logic, `masks[v]` accumulates `push_mask` from parents.
    `push_mask` includes `u` and ancestors of `u`.
    It never adds `v` to `masks[v]` directly.
    Is it possible for $v$ to be in `masks[v]`?
    Only if there is a path from $v$ to $v$. i.e., cycle involving $v$.
    But if cycle exists, we return `[]`.
    So in the DAG case, $v$ will never reach itself.
    So `bin(masks[v]).count('1')` correctly counts "other" vertices.

    Wait, is it possible that `edges` list has edges like `[0, 1]` and `[0, 1]`?
    Spec: "no self-loops or duplicate edges". So no need to deduplicate.

    Input parsing:
    `n = data["n"]`
    `edges = data["edges"]`
    If `edges` is missing? Spec says input has "n" and "edges".
    
    Constraints check:
    $n \le 50$.
    Edges $\le 150$.
    Time limit 10s.
    This approach is extremely efficient.

    Let's write the code structure.

```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    
    if n == 0:
        return []
    
    adj = [[] for _ in range(n)]
    in_degree = [0] * n
    
    for u, v in edges:
        adj[u].append(v)
        in_degree[v] += 1
        
    # Kahn's algorithm for Topological Sort and Cycle Detection
    queue = []
    for i in range(n):
        if in_degree[i] == 0:
            queue.append(i)
            
    order = []
    # Using a list as queue, pop from end is O(1)
    while queue:
        u = queue.pop()
        order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    if len(order) < n:
        return []
    
    # Compute ancestors using bitmasks
    masks = [0] * n
    
    for u in order:
        # Ancestors of u are already computed in masks[u]
        # We need to propagate (ancestors of u) U {u} to neighbors
        push_mask = masks[u] | (1 << u)
        
        for v in adj[u]:
            masks[v] |= push_mask
            
    # Count set bits
    result = []
    for m in masks:
        # count '1' bits
        cnt = 0
        temp = m
        while temp > 0:
            temp &= (temp - 1)
            cnt += 1
        result.append(cnt)
        
    return result
```
    
    Wait, `queue.pop()` pops from end (LIFO). This is DFS-like topological sort?
    Actually Kahn's algorithm usually uses a Queue (FIFO), but for Topological Sort any order that respects dependencies works. A list as a stack works fine for Topological Sort validity?
    Yes. If $u$ is ready (in-degree 0), it can be processed. Order among ready nodes doesn't matter for correctness of topo sort, just that parents are processed before children. Since we only add to queue when in-degree hits 0, dependencies are satisfied.
    However, standard Kahn's uses a queue. `pop(0)` is $O(N)$, `pop()` is $O(1)$. With $N=50$, doesn't matter. But `pop()` is faster.
    
    Wait, logic check on propagation order.
    If we use stack (LIFO), does it affect correctness?
    We iterate `order` list sequentially. The `order` list is constructed by popping from queue.
    If queue is a stack, `order` will have children appearing after parents?
    Wait. In Kahn's algo, we only add $v$ to queue when in-degree becomes 0. This means all parents of $v$ have been popped and processed.
    So $v$ enters the queue *after* its parents have been popped.
    So in `order`, $v$ will appear *after* its parents?
    Wait.
    Parent $p$ is in queue. Popped. Added to `order`.
    $p$ decreases in-degree of child $c$.
    If $c$'s in-degree becomes 0, $c$ added to queue.
    So $c$ is added to queue *after* $p$ is popped.
    Since $p$ is already in `order`, and $c$ will be popped later (eventually), $c$ appears after $p$ in `order`.
    Yes, topological order property holds regardless of FIFO vs LIFO choice for the queue.
    
    Wait, what if multiple parents?
    All parents must be processed before child is added. So all parents appear before child in `order`.
    Correct.

    One optimization/correction:
    In `for v in adj[u]: masks[v] |= push_mask`.
    Is it possible that we update `masks[v]` multiple times? Yes.
    Is it possible that we process $v$ before all parents have updated it?
    We iterate `u` in `order`. When we are at `u`, we read `masks[u]`.
    `masks[u]` must be fully accumulated from all parents.
    Since all parents of $u$ appear before $u$ in `order`, they have already executed the loop `for v in adj[parent]: masks[v] |= ...`.
    One of those neighbors is $u$.
    So yes, `masks[u]` is fully ready when we reach $u$ in the loop.
    
    Wait, check the edge direction carefully.
    Input: `edges` contains `[u, v]`, meaning $u \to v$.
    Adjacency list `adj[u].append(v)`. Correct.
    Propagation: From $u$ to neighbors $v$.
    Path goes $parent \to u \to v$.
    Ancestors of $u$ + $u$ become ancestors of $v$.
    Logic: `masks[v] |= masks[u] | (1 << u)`. Correct.
    
    Wait, what if there are multiple edges between nodes? (Ruled out).
    What if parallel paths? Handled by mask OR.
    
    Let's check bit counting implementation.
    `temp &= (temp - 1)` is Brian Kernighan's algorithm. Efficient.
    Or just `bin(m).count('1')`.
    Since no imports, `bin` is builtin?
    Builtins list includes `bin`. Yes.
    `bin(m).count('1')` is cleaner and likely fast enough for $N=50$.
    
    Wait, "Methods of built-in types... may be used".
    `str.count` is a method of str. `bin` returns str.
    So `bin(m).count('1')` is valid.
    
    Let's check variable names and forbidden functions.
    Forbidden: `eval`, `exec`, etc.
    Used: `range`, `len`, `list`, `int`, `bool`, `str`, `print` (not used), `append`, `pop`, `count`.
    All allowed.
    
    Check variable shadowing or naming issues.
    No double underscores.
    
    Wait, "return [] if a cycle exists".
    My code checks `len(order) < n`.
    Is it possible that `len(order) == n` but there is a cycle?
    No. In a finite graph, if topological sort visits all vertices, the graph is a DAG.
    If there is a cycle, at least one vertex in the cycle (and its descendants in terms of reachability within the component?) won't have in-degree 0 at any point (or rather, nodes in the cycle never get reduced to 0 in-degree because they depend on each other).
    Actually, if there is a cycle, none of the nodes in the cycle can ever have in-degree 0 *unless* edges from outside break it? No, internal edges maintain dependency.
    If $u \to v$ and $v \to u$, in-degrees are at least 1 each. They never drop to 0 unless we remove edges, but we don't.
    Wait, Kahn's algo simulates removal.
    Initially count in-degrees.
    Remove nodes with 0 in-degree.
    In a cycle, every node has in-degree $\ge 1$ (from within cycle).
    So no node in cycle enters queue initially.
    And since we only remove edges from processed nodes, and no node in cycle is processed, edges inside cycle remain.
    So nodes in cycle never enter queue.
    So `len(order) < n` correctly detects cycles.
    
    Corner case: Graph with 1 node, self loop?
    Spec: "no self-loops".
    But if input had `[[0, 0]]`, $n=1$.
    In-degree of 0 is 1. Queue empty. Order empty. Len 0 < 1. Returns []. Correct.
    (Though spec says no self loops).
    
    Corner case: $n=1$, edges `[[]]`.
    In-degree 0. Queue `[0]`. Pop 0. Order `[0]`. Len 1 == 1.
    Masks: `masks[0]=0`. Loop `u=0`. Neighbors empty.
    Result `[0]`. Correct.
    
    Corner case: $n=2$, edges `[[]]`.
    Result `[0, 0]`. Correct.
    
    Wait, result for $n=1$ with no edges should be `[0]`.
    Because 0 distinct *other* vertices have path to 0.
    Yes.
    
    Let's re-read carefully: "Return a list whose entry v is the number of distinct other vertices having a directed path to v."
    If $n=1$, vertex 0. Path from other vertices? None. Count 0.
    My code produces 0.
    
    Wait, check constraints on integer size.
    Python handles large integers. `1 << 50` is fine.
    
    One detail: The problem statement says "Result JSON Schema...".
    Just need to return list of ints.
    
    Let's verify the "no imports" rule.
    My code uses no imports.
    
    Check function signature: `def solve(data):`.
    Input is dict.
    
    Wait, I used `queue` as a list and `pop()`.
    Is that allowed? Yes.
    
    Double check the time limit logic.
    If graph is dense (150 edges), $N=50$.
    Topo sort: fast.
    Loop over 50 nodes. Inner loop over edges. Total edge visits = 150.
    Bitwise OR on integers of size 50 bits. Very fast.
    Bit count: 50 calls to `bin` or loop. Fast.
    Total time negligible.
    
    Is there any tricky case with labels?
    "labels 0..n-1". So vertices are exactly $0$ to $n-1$.
    Input edges use these labels.
    If input uses labels outside range? Spec implies valid input.
    
    One potential issue:
    `data` might be modified?
    "When solve returns, data must compare equal (==) to its value before the call".
    My code reads `n` and `edges`. It creates new lists `adj`, `in_degree`, `masks`.
    It does not modify `data` or `edges` list (though iterating over it is fine).
    Wait, `edges` is a list of lists.
    I iterate `for u, v in edges`. This doesn't modify `edges`.
    So input data is preserved.
    
    Wait, what if `edges` contains tuples? Spec says `[u,v]` (lists).
    Iterating works for both.
    
    What if `data` has extra keys? We ignore them.
    
    Let's refine the solution to be clean and minimal.

```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    
    # If n is 0, result is empty list (handled by logic below but explicit check ok)
    if n == 0:
        return []
        
    adj = [[] for _ in range(n)]
    in_degree = [0] * n
    
    for u, v in edges:
        adj[u].append(v)
        in_degree[v] += 1
        
    # Topological Sort using Kahn's Algorithm
    queue = [i for i in range(n) if in_degree[i] == 0]
    order = []
    
    # Using a list as a stack for queue (pop() is O(1))
    while queue:
        u = queue.pop()
        order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    # If not all nodes are in topological order, there is a cycle
    if len(order) < n:
        return []
    
    # Compute ancestor counts using bitmasks
    masks = [0] * n
    
    # Process nodes in topological order
    for u in order:
        # Mask for node u including all its ancestors and u itself
        mask_with_u = masks[u] | (1 << u)
        
        # Propagate to neighbors
        for v in adj[u]:
            masks[v] |= mask_with_u
            
    # Count bits in each mask
    result = []
    for m in masks:
        # Using bin().count('1') is safe and clean
        # Or manual count. bin() returns '0b...', so count '1's.
        res = 0
        while m > 0:
            m &= (m - 1)
            res += 1
        result.append(res)
        
    return result
```

    Wait, checking `bin().count('1')` vs loop.
    Loop is slightly more verbose but avoids string allocation. Given constraints, either is fine. Loop is "safer" regarding overhead? No, strings are optimized. But loop uses only ints.
    I'll stick to loop or `bin`. Actually `bin().count('1')` is very pythonic. But wait, `bin` creates a string. With $N=50$, string length ~60. 50 times. Trivial.
    However, the prompt says "Methods of built-in types ... may be used". `str.count` is fine.
    Let's use the loop to be purely numeric and avoid any ambiguity about allowed methods (though `count` is standard). Actually `bin` is builtin.
    
    Wait, what if `masks[u]` is 0? `m & (m-1)` works correctly (loop doesn't run, res=0).
    
    One edge case: `in_degree` modification.
    We modify `in_degree` array. Is that allowed?
    "When solve returns, data must compare equal (==) to its value before the call".
    `data` is the dictionary. `data["edges"]` refers to the list object passed in.
    I don't modify `data` or `edges`.
    I create new lists `adj`, `in_degree`, `masks`.
    So `data` remains unchanged.
    
    Wait, I used `queue = [i for i in range(n) if in_degree[i] == 0]`.
    This creates a new list. Safe.
    
    Is it possible that `edges` is not a list of lists but list of tuples?
    "edges":[[u,v],...] -> List of lists.
    Even if tuples, unpacking `u, v` works.
    
    Check strict constraints on imports. "No imports".
    My code has no imports.
    
    Check for "classes, decorators". None used.
    Check for "docstring". None.
    Check for "if __name__ guard". None.
    
    Is `pop` allowed? Yes, method of list.
    
    Let's double check the cycle detection logic.
    If graph is $0 \to 1$, $1 \to 2$, $2 \to 1$. (Cycle 1-2).
    In-degrees: $0:0, 1:2 (from 0, 2), 2:1 (from 1)$.
    Queue starts with `[0]`.
    Pop 0. Order `[0]`.
    Neighbors of 0: `[1]`.
    Decrement `in_degree[1]` from 2 to 1. Not 0.
    Queue empty.
    Loop ends.
    `len(order)` is 1. $n=3$.
    $1 < 3$, returns `[]`. Correct.
    
    What if graph is $0 \leftrightarrow 1$ (cycle) and $2$ isolated.
    In-degrees: $0:1, 1:1, 2:0$.
    Queue `[2]`.
    Pop 2. Order `[2]`. Neighbors empty.
    Queue empty.
    Len 1 < 3. Returns `[]`. Correct.
    
    Wait, "Return [] if a cycle exists".
    Does it matter which nodes are in the cycle? No. Just existence.
    
    What about $n=0$?
    My code: `if n == 0: return []`.
    Also logic would handle it: range(0) -> empty queue, empty order, len(0)==0, masks=[], result=[].
    But explicit check is safer/clearer.
    
    Wait, what if input $n$ is large but edges list is sparse? $N \le 50$. It's small.
    
    Let's check variable naming conflicts.
    `order`, `masks`, `adj`, `in_degree`, `queue`. All local. Safe.
    
    One detail:
    The problem statement: "Return [] if a cycle exists; n=0 returns []."
    If $n=0$, list is empty. `[]` is correct.
    My explicit check handles it.
    
    Wait, could there be a case where `in_degree` logic fails?
    Only if edges contain invalid vertices (>= n).
    Spec: "labels 0..n-1". Implies valid.
    
    Let's consider efficiency of bitmask propagation.
    If we have a chain $0 \to 1 \to 2 \dots \to 49$.
    Masks will be:
    0: 0 -> push 1 (bit 0) to 1.
    1: mask 1 -> push 3 (bits 0,1) to 2.
    2: mask 3 -> push 7 (bits 0..2) to 3.
    ...
    Mask size grows. Bitwise OR of 50-bit int is fast.
    Operations count: 50 nodes. Each has 1 neighbor. 50 ops.
    
    What if complete graph? $N=50$, edges $\approx 1225$?
    But max edges 150. So graph is sparse.
    Complexity is dominated by $O(E \cdot N / \text{word})$. Very fast.
    
    Let's check the output format again.
    "Result JSON Schema: {"type":"array","items":{"type":"integer"}}".
    Python list of ints serializes to JSON array of integers.
    My code returns list of ints.
    
    Final verification of the algorithm logic for correctness of ancestor counting.
    We want count of distinct $u$ such that path $u \to v$ exists.
    Algorithm:
    Topological sort ensures we process nodes in dependency order.
    When processing $u$, `masks[u]` contains all nodes $x$ such that path $x \to u$ exists?
    Wait. `masks[u]` accumulates from parents.
    Base case: Nodes with no incoming edges (sources).
    Their masks are initialized to 0. Correct, as no ancestors.
    When processing a source $s$, it pushes `1 << s` to neighbors.
    So neighbor $v$ gets bit $s$ set in mask.
    This means $s$ is an ancestor of $v$.
    If there is a path $s \to w \to v$.
    1. Process $s$. Pushes bit $s$ to $w$. `masks[w]` has bit $s$.
    2. Process $w$. Reads `masks[w]` (has bit $s$). Computes `mask_with_u` = `masks[w] | (1 << w)`. This has bits $\{s, w\}$.
       Pushes to $v$. `masks[v]` gets bits $\{s, w\}$ OR'ed.
    3. So `masks[v]` ends up with bits $\{s, w\}$.
    Count is 2. Ancestors of $v$ are $s, w$. Correct.
    
    What if multiple paths?
    $s_1 \to v$, $s_2 \to v$.
    1. Process $s_1$. Pushes bit $s_1$ to $v$. `masks[v]` has $\{s_1\}$.
    2. Process $s_2$. Pushes bit $s_2$ to $v$. `masks[v]` gets $\{s_1, s_2\}$.
    Count 2. Correct.
    
    What if $s \to u \to v$ and $s \to v$ (diamond).
    1. Process $s$. Pushes bit $s$ to $u$ and $v$.
       `masks[u]` has $\{s\}$.
       `masks[v]` has $\{s\}$ (from direct edge).
    2. Process $u$. Reads `masks[u]` ($\{s\}$). Pushes $\{s, u\}$ to $v$.
       `masks[v]` becomes $\{s\} | \{s, u\} = \{s, u\}$.
    Count 2. Ancestors of $v$ are $s, u$. Correct (path $s \to v$ and $s \to u \to v$). Distinct vertices $\{s, u\}$.
    
    Wait, does `masks[v]` contain $v$?
    No, bits are only added from predecessors.
    Unless cycle, which is excluded.
    
    Seems perfect.

    One small thing:
    Input `edges` might be empty list.
    Code handles it.
    Input `n` might be 1, edges empty.
    Code handles it.
    
    Check variable naming "data". It's the argument.
    `data["n"]` access is fine.
    
    Check constraints on return type.
    "Return a list...".
    Code returns list.
    
    Check "no NaN or infinity". Integers are safe.
    
    One final check on cycle detection with `in_degree`.
    If the graph has a cycle, nodes in cycle never reach 0 in-degree.
    Wait, what if a node is part of a cycle but also has an incoming edge from outside?
    e.g. $0 \to 1$, $1 \to 2$, $2 \to 1$.
    In-degrees: $0:0, 1:2 (from 0, 2), 2:1 (from 1)$.
    Queue starts with `[0]`.
    Pop 0. Update 1. `in_degree[1]` becomes 1.
    Queue empty.
    Order `[0]`.
    Len 1 != 3. Returns `[]`.
    Correct. The cycle $1-2$ prevents processing of 1 and 2.
    
    What if $1 \to 2$, $2 \to 1$. (Isolated cycle).
    In-degrees: $1:1, 2:1$.
    Queue empty.
    Order `[]`.
    Len 0 != 2. Returns `[]`.
    Correct.
    
    What if input is malformed? e.g. edge `[5, 6]` with $n=2$.
    Spec says valid input. We assume valid.
    If invalid, IndexError would occur. But we don't need to handle.
    
    Is it possible that `data` contains keys not "n" or "edges"?
    We ignore them.
    
    Code looks solid.

    Wait, I should check the "no docstring" rule.
    The prompt says: "No docstring, if __name__ guard or other top-level statement."
    So I must not include comments?
    "The top level may contain only function definitions and names assigned a literal constant... No docstring".
    Comments inside function are fine?
    "Other top-level statement" usually refers to executable code.
    Comments `#` are ignored by parser, but technically text.
    However, usually "No docstring" means don't put `"""..."""`.
    But to be safe, I will minimize comments or keep them brief?
    Actually, standard Python comments are fine inside functions. The restriction is on top-level statements.
    Wait, "The top level may contain only function definitions and names assigned a literal constant".
    Comments don't count as statements.
    But to be extremely safe and clean, I'll keep code self-explanatory or minimal comments.
    
    Let's refine the solution to be compact and compliant.

```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    if n == 0:
        return []
    
    adj = [[] for _ in range(n)]
    in_degree = [0] * n
    for u, v in edges:
        adj[u].append(v)
        in_degree[v] += 1
        
    queue = [i for i in range(n) if in_degree[i] == 0]
    order = []
    while queue:
        u = queue.pop()
        order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    if len(order) < n:
        return []
    
    masks = [0] * n
    for u in order:
        m = masks[u] | (1 << u)
        for v in adj[u]:
            masks[v] |= m
            
    result = []
    for m in masks:
        c = 0
        while m > 0:
            m &= m - 1
            c += 1
        result.append(c)
        
    return result
```
    Wait, `m & (m-1)` logic.
    `m &= m - 1` modifies `m`.
    Wait, in Python `m &= m - 1` is valid.
    But `m` is local variable.
    However, I used `m` as loop variable name in list comprehension? No.
    In the bit counting loop:
    `for m in masks:` iterates values. `m` is integer (immutable).
    Wait, `m` inside `while m > 0` loop reassigns `m`.
    This is fine, `m` is local to that scope?
    Actually `m` is the loop variable. Reassigning it affects the loop variable?
    In Python, loop variables leak to function scope, but reassigning `m` inside the body just changes the local name `m`. It does not affect the list or the iteration value (since integers are passed by value/reference, but loop takes next item from iterator).
    Wait, `for m in masks:` gets next integer.
    If I change `m`, it doesn't affect subsequent iterations.
    So it's safe.
    
    However, cleaner to use a different variable name for temp bit count to avoid confusion.
    `temp = m`.
    
    Also, `m & (m - 1)` works.
    
    Let's double check `bin(m).count('1')` approach vs manual loop.
    Manual loop is very explicit.
    
    One detail:
    The problem says "Return [] if a cycle exists".
    My code does that.
    
    Wait, what about the return type for $n=0$?
    `if n == 0: return []`.
    Code returns list.
    
    Check constraints on integer size again.
    Python integers have arbitrary precision.
    $1 << 50$ fits easily.
    
    One potential optimization:
    If `adj[u]` is empty, we skip inner loop.
    List comprehension handles it.
    
    Final check on "no self-loops or duplicate edges".
    If input had duplicates, in-degree count would be higher, but topo sort logic still holds (just more decrements). But duplicates might affect `in_degree` initialization if not careful?
    Wait, if edge `[0, 1]` appears twice.
    `adj[0]` has two `1`s.
    `in_degree[1]` becomes 2.
    Processing 0: decrement `in_degree[1]` twice.
    It works fine even with duplicates.
    But spec says no duplicates.
    
    Wait, what if `edges` is empty but $n > 0$?
    Queue has all nodes. Order has all nodes.
    Loop runs. `masks` stay 0. Result `[0]*n`. Correct.
    
    What if graph is just 2 nodes with edge `1 -> 0` (reverse order).
    $n=2$, edges `[[1, 0]]`.
    In-degrees: `0:1, 1:0`.
    Queue `[1]`.
    Pop 1. Order `[1]`.
    Neighbors of 1: `[0]`.
    Decr `in_degree[0]` to 0. Push 0.
    Pop 0. Order `[1, 0]`.
    Neighbors empty.
    Order len 2. OK.
    Masks init `[0, 0]`.
    Process 1 (u=1): `masks[1]` is 0. `push_mask` = `0 | (1<<1)` = 2.
       Neighbors `[0]`. `masks[0] |= 2` -> 2.
    Process 0 (u=0): `masks[0]` is 2. `push_mask` = `2 | (1<<0)` = 3.
       Neighbors empty.
    Result:
    masks[0] = 2 (binary 10). Bits: 1. Count 1.
    masks[1] = 0. Count 0.
    Output `[1, 0]`.
    Vertex 0 has ancestor 1. Correct.
    Vertex 1 has no ancestors. Correct.
    
    Wait, order of result list corresponds to vertices $0 \dots n-1$.
    My code appends to `result` in order of `masks` (which is index $0 \dots n-1$).
    Wait, `for m in masks:` iterates indices $0$ to $n-1$.
    So `result[0]` corresponds to vertex 0.
    Yes.
    
    Wait, in the example above, result was `[1, 0]`.
    Vertex 0 count 1. Vertex 1 count 0.
    List is `[count(0), count(1)]`.
    Correct.

    Double check: "Return a list whose entry v is the number...".
    Yes, index $v$ corresponds to vertex $v$.
    
    Looks good.

    One tiny thing:
    Input `data` keys might be case sensitive? "n", "edges".
    Assume standard.
    
    Final check on code structure requirements.
    - Function `solve(data)`.
    - No imports.
    - No classes/decorators.
    - Top level minimal.
    
    Code:
```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    if n == 0:
        return []
    
    adj = [[] for _ in range(n)]
    in_degree = [0] * n
    for u, v in edges:
        adj[u].append(v)
        in_degree[v] += 1
        
    queue = [i for i in range(n) if in_degree[i] == 0]
    order = []
    while queue:
        u = queue.pop()
        order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    if len(order) < n:
        return []
    
    masks = [0] * n
    for u in order:
        push_mask = masks[u] | (1 << u)
        for v in adj[u]:
            masks[v] |= push_mask
            
    result = []
    for m in masks:
        count = 0
        while m > 0:
            m &= (m - 1)
            count += 1
        result.append(count)
        
    return result
```
    Wait, `queue` initialization list comprehension creates a list.
    `range(n)` is safe.
    
    Is `pop()` allowed? Yes.
    
    Wait, I used `m` in loop and modified it.
    In the bit counting loop:
    `for m in masks:`
    Inside: `while m > 0: m &= (m - 1)`.
    This modifies the loop variable `m`.
    Is this safe?
    In Python, iterating over a list yields values.
    If I change `m`, it just changes the local name `m` to point to a new int.
    It does not affect the list `masks` or the iteration process.
    So it is safe.
    But to be 100% clear and avoid any weirdness, I'll use `temp`.
    
```python
    for m in masks:
        count = 0
        temp = m
        while temp > 0:
            temp &= (temp - 1)
            count += 1
        result.append(count)
```
    This is cleaner.

    Wait, `masks` contains integers. Integers are immutable.
    Iteration yields integer object.
    Rebinding `m` to new integer is fine.
    
    One optimization: `bin(m).count('1')` is implemented in C and very fast.
    `temp &= (temp-1)` loop runs $k$ times where $k$ is number of set bits. Max 50.
    Very fast. Both are fine.
    
    Wait, the bit count logic `m &= (m - 1)` clears the lowest set bit.
    Correct.
    
    I will use the loop method to be dependency-free (though bin is builtin).
    Actually `bin` is a builtin function. It's allowed.
    But loop is "algorithmic" and fits the spirit.
    
    Wait, checking the constraint: "Only these builtins exist: ...".
    `bin` is in the list.
    So `bin(m).count('1')` is perfectly valid.
    Maybe slightly more readable?
    But loop is fine too. I'll stick to loop or bin, doesn't matter.
    Let's use `bin(m).count('1')` for brevity?
    Actually `bin` returns string with '0b'. `count('1')` counts '1's.
    Is there any risk? No.
    
    However, to be extremely robust against any hidden environment quirks (though unlikely), the integer arithmetic approach is pure.
    
    Let's check if `m` can be negative?
    No, masks are non-negative.
    
    One detail: The prompt mentions "Results are graded after JSON serialization and parsing."
    So exact format matters.
    List of integers.
    
    Let's verify the cycle return again.
    If cycle, returns `[]`.
    Is `[]` a valid JSON array? Yes.
    Does it match schema `{"type":"array","items":{"type":"integer"}}`?
    An empty array is a subtype of array with any item type constraint (vacuously true).
    So yes.
    
    Wait, if $n=0$, result `[]`.
    If cycle, result `[]`.
    Seems consistent.
    
    Final check: "data must compare equal (==) to its value before the call".
    My code does not mutate `data` or `edges` list content.
    It creates new structures.
    Safe.
    
    Wait, `queue = [i for i in range(n) if in_degree[i] == 0]`
    This creates a new list.
    `adj`, `in_degree` are new lists.
    `order` is new list.
    `masks` is new list.
    `result` is new list.
    Safe.

    Wait, `edges` is a reference to the list in `data`.
    I iterate over it. I don't modify it.
    So `data["edges"]` remains same list object with same contents.
    Correct.
    
    Is it possible `data` is modified by reference?
    Python passes dict by reference.
    If I did `data["n"] = 5`, it would change.
    But I only read.
    
    Wait, "restoring temporary changes is fine".
    Since I don't make changes, even safer.

    Final Code assembly.

```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    if n == 0:
        return []
    
    adj = [[] for _ in range(n)]
    in_degree = [0] * n
    for u, v in edges:
        adj[u].append(v)
        in_degree[v] += 1
        
    queue = [i for i in range(n) if in_degree[i] == 0]
    order = []
    while queue:
        u = queue.pop()
        order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    if len(order) < n:
        return []
    
    masks = [0] * n
    for u in order:
        push_mask = masks[u] | (1 << u)
        for v in adj[u]:
            masks[v] |= push_mask
            
    result = []
    for m in masks:
        c = 0
        temp = m
        while temp > 0:
            temp &= (temp - 1)
            c += 1
        result.append(c)
        
    return result
```
    Wait, `masks[u] | (1 << u)`.
    If $u$ is large, $1 << u$ is large int.
    Python handles it.
    
    Wait, `queue` is a list. `pop()` removes last element.
    This is valid for Kahn's algo?
    Yes. Any valid topological order works.
    Order of processing nodes with in-degree 0 doesn't affect validity or correctness of ancestor sets (since set union is associative/commutative).
    
    Wait, if we use stack (LIFO), does it change the `order`?
    Yes, but it remains a valid topological sort.
    Proof: If $u \to v$, then $in\_degree[v] \ge 1$.
    $v$ can only be added to queue after $u$ is popped and decrements in-degree.
    So $u$ is always popped before $v$ is added.
    Thus $u$ appears in `order` before $v$.
    So topological property holds.
    
    Double check logic for "distinct other vertices".
    My mask includes ancestors of $u$, and adds $u$.
    Since $u$ is not an ancestor of itself (DAG), it adds a new distinct vertex.
    Propagates to neighbors.
    Neighbor $v$ accumulates these.
    Does $v$ ever add itself?
    When processing $v$, `push_mask` includes `masks[v] | (1 << v


## Entire final response

```python
def solve(data):
    n = data["n"]
    edges = data["edges"]
    
    # If there are no vertices, return empty list
    if n == 0:
        return []
    
    # Build adjacency list and compute in-degrees
    adj = [[] for _ in range(n)]
    in_degree = [0] * n
    for u, v in edges:
        adj[u].append(v)
        in_degree[v] += 1
        
    # Kahn's algorithm for Topological Sort and Cycle Detection
    # Initialize queue with nodes having no incoming edges
    queue = [i for i in range(n) if in_degree[i] == 0]
    order = []
    
    while queue:
        u = queue.pop()  # Use list as stack (LIFO), valid for topo sort
        order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    # If topological sort doesn't include all nodes, a cycle exists
    if len(order) < n:
        return []
    
    # Compute ancestor counts using bitmasks
    # masks[i] will store a bitmask of all vertices having a path to i
    masks = [0] * n
    
    # Process nodes in topological order
    for u in order:
        # The set of ancestors for neighbors includes all ancestors of u, plus u itself
        push_mask = masks[u] | (1 << u)
        
        # Propagate to all children
        for v in adj[u]:
            masks[v] |= push_mask
            
    # Count the number of set bits in each mask to get the number of distinct other vertices
    result = []
    for m in masks:
        count = 0
        temp = m
        while temp > 0:
            temp &= (temp - 1)
            count += 1
        result.append(count)
        
    return result
```
