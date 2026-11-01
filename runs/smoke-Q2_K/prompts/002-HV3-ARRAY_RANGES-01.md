# PENDING

Question: HV3-ARRAY_RANGES-01 | Quantization: Q2_K | Status: not_started

Solution correct: None | Strict response correct: None

Inference seconds: None | Decode tokens/s: None | Thinking budget exhausted: None | Output cap reached: None

## Exact prompt

Algorithmic Python task. data={"a":list of signed integers in [-20,20],"k":integer in [1,30]}; 0<=len(a)<=120.

Return the largest length of a nonempty contiguous subarray with sum<=k; 0 if none.
Result JSON Schema: {"type":"integer"}. Results are graded after JSON serialization and parsing. Use Python int (not bool) for integer results, bool for booleans, list or tuple for JSON arrays, dict with string keys for objects, None for null; no NaN or infinity. Normalized JSON types and values must match exactly.
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



## Entire final response


