<div align="center">
<pre style="color: #0095ff; font-weight: bold;">
```
███████████                                ██████   █████           ███                  
░█░░░░░░███                                ░░██████ ░░███           ░░░                   
░     ███░    ██████  ████████   ██████     ░███░███ ░███   ██████  ████   █████   ██████ 
     ███     ███░░███░░███░░███ ███░░███    ░███░░███░███  ███░░███░░███  ███░░   ███░░███
    ███     ░███████  ░███ ░░░ ░███ ░███    ░███ ░░██████ ░███ ░███ ░███ ░░█████ ░███████ 
  ████     █░███░░░   ░███     ░███ ░███    ░███  ░░█████ ░███ ░███ ░███  ░░░░███░███░░░  
 ███████████░░██████  █████    ░░██████     █████  ░░█████░░██████  █████ ██████ ░░██████ 
░░░░░░░░░░░  ░░░░░░  ░░░░░      ░░░░░░     ░░░░░    ░░░░░  ░░░░░░  ░░░░░ ░░░░░░   ░░░░░░  

 ███████████                               █████                                          
░░███░░░░░███                             ░░███                                           
 ░███    ░███  ██████  ████████    ██████  ░███████                                       
 ░██████████  ███░░███░░███░░███  ███░░███ ░███░░███                                      
 ░███░░░░░███░███████  ░███ ░███ ░███ ░░░  ░███ ░███                                      
 ░███    ░███░███░░░   ░███ ░███ ░███  ███ ░███ ░███                                      
 ███████████ ░░██████  ████ █████░░██████  ████ █████                                     
░░░░░░░░░░░   ░░░░░░  ░░░░ ░░░░░  ░░░░░░  ░░░░ ░░░░░                                      
```
</pre>
</div>

# ZeroNoiseBench

A benchmark testing LLMs on simple character-level and reasoning tasks they commonly fail — string reversal, counting, math gotchas, pattern sequences, encoding, spatial/positional, logic traps, and format parsing.

---

## Repo Structure

```
ZeroNoiseBench/
├── eval/
│   └── evaluate.py          # Scoring script
├── results/
│   └── .gitkeep             # Drop your model response files here
├── tasks/
│   ├── string_ops.json
│   ├── counting.json
│   ├── math_gotchas.json
│   ├── pattern_sequences.json
│   ├── encoding.json
│   ├── spatial_positional.json
│   ├── logic_traps.json
│   └── format_parsing.json
└── README.md
```

---

## Task Schema

Each task is a JSON object with the following fields:

```json
{
  "id": "string_ops_L1_001",
  "category": "string_ops",
  "difficulty": "L1",
  "prompt": "Reverse the string: hello",
  "expected_output": "olleh",
  "eval_type": "exact"
}
```

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier: `{category}_{difficulty}_{index}` |
| `category` | string | One of the 8 benchmark categories |
| `difficulty` | string | `L1`, `L2`, or `L3` |
| `prompt` | string | The instruction given to the model |
| `expected_output` | string | The correct answer |
| `eval_type` | string | `"exact"` or `"extract"` (see Eval Types below) |

### Eval Types

- **exact** — The model response (whitespace-stripped) must exactly match `expected_output` (case-sensitive).
- **extract** — The `expected_output` string must appear anywhere inside the model response (case-insensitive). Useful for tasks where the answer is embedded in an explanation.

---

## Categories

| # | Category | Tasks | Description |
|---|---|---|---|
| 1 | `string_ops` | 30 | Reversal, slicing, character swaps, interleaving |
| 2 | `counting` | 30 | Count characters, words, vowels, substrings |
| 3 | `math_gotchas` | 30 | Order of operations, floating-point edge cases, trick questions |
| 4 | `pattern_sequences` | 30 | Continue numeric, alphabetic, and mixed sequences |
| 5 | `encoding` | 30 | Caesar cipher, Base64, ROT13, binary/hex conversions |
| 6 | `spatial_positional` | 30 | Nth character, positional indexing, grid navigation |
| 7 | `logic_traps` | 30 | Classic logic puzzles, common misconceptions, negation traps |
| 8 | `format_parsing` | 30 | Extract fields from structured text (CSV, JSON snippets, tables) |

**Total: 240 tasks**

---

## Difficulty Levels

| Level | Description |
|---|---|
| **L1** | Short input, simple transformation, unambiguous answer |
| **L2** | Medium-length input, multi-step reasoning, or slight obfuscation |
| **L3** | Long or complex input, random-looking data, chained operations |

---

## Running the Evaluator

```bash
python eval/evaluate.py --responses results/my_model.json
```

The evaluator:
1. Loads all task definitions from `tasks/*.json`.
2. Matches each response entry to its task by `id`.
3. Applies the appropriate scoring rule (`exact` or `extract`).
4. Prints a per-task pass/fail table, per-category accuracy, and overall accuracy.
5. Saves a `_scored.json` file alongside your responses file.

### Example output

```
================================================================
ZeroNoiseBench Evaluation Results
================================================================
Task ID               Category           Diff  Pass   Notes
----------------------------------------------------------------
string_ops_L1_001     string_ops         L1    PASS   ok
counting_L1_001       counting           L1    FAIL   expected: '3'
...
----------------------------------------------------------------

Per-Category Accuracy:
----------------------------------------
  counting            8/30   ( 26.7%)
  encoding           15/30   ( 50.0%)
  string_ops         22/30   ( 73.3%)
  ...

Overall Accuracy: 112/240  (46.7%)

Scored results saved to: results/my_model_scored.json
```

---

## Submitting Results

1. Run your model against every prompt in `tasks/*.json`.
2. Collect responses as a JSON array:

```json
[
  {"id": "string_ops_L1_001", "model_response": "olleh"},
  {"id": "counting_L1_001",   "model_response": "3"},
  ...
]
```

3. Save the file to `results/<your_model_name>.json`.
4. Run the evaluator to generate `results/<your_model_name>_scored.json`.
5. Open a pull request adding both files to the `results/` directory.

---

## License

MIT
