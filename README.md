# AgentBench Lite

**A research-oriented framework for evaluating the reliability of tool-using AI agents.**

AgentBench Lite is a Python project designed to investigate how bounded recovery strategies affect the reliability of agents that interact with tools. It provides a deterministic benchmark environment for comparing a baseline agent against an agent that can retry after selected tool failures.

The current implementation uses scripted mock-model actions and deterministic tools, making experiments reproducible and suitable for testing agent execution, error handling, validation, recovery behavior, and benchmark metrics.

## Table of Contents

- [Objectives](#objectives)
- [Research Question](#research-question)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Tests](#running-the-tests)
- [Running the Benchmark](#running-the-benchmark)
- [Benchmark Design](#benchmark-design)
- [Evaluation Metrics](#evaluation-metrics)
- [Experimental Results](#experimental-results)
- [Reproducibility](#reproducibility)
- [Limitations](#limitations)
- [Future Work](#future-work)

## Objectives

The main objectives of AgentBench Lite are to:

1. Implement a modular agent execution framework with structured tool interactions.
2. Validate tool actions and arguments before execution.
3. Handle tool errors using structured error information.
4. Compare baseline execution with bounded recovery.
5. Evaluate task completion, execution overhead, and failure behavior.
6. Persist experiment results in machine-readable JSON files.
7. Provide automated tests for core components and benchmark functionality.

## Research Question

**Does allowing an agent one bounded corrective retry improve task completion enough to justify the additional execution overhead?**

The project investigates this question by running the same benchmark tasks under two strategies:

- **Baseline:** Executes without corrective recovery retries.
- **Recovery:** Allows one corrective retry for eligible tool failures, subject to configured execution limits.

The current experiment establishes a reproducible testing foundation. Its findings apply to the implemented deterministic benchmark and should not be interpreted as proof of equivalent improvements in real-world LLM agents.

## Features

### Agent execution

- Scripted mock-model interface through `MockModel`.
- Configurable execution strategies.
- Maximum-step limits.
- Bounded retry configuration.
- Structured terminal statuses and execution history.

### Tool system

The default tool registry includes three tools:

| Tool             | Functionality                                       |
| ---------------- | --------------------------------------------------- |
| `calculator`     | Addition, subtraction, multiplication, and division |
| `unit_converter` | Kilometre/mile and Celsius/Fahrenheit conversions   |
| `mock_lookup`    | Retrieves predefined information for supported keys |

The tools are deterministic and do not require external APIs or network access.

### Validation and error handling

- Tool-name and argument validation.
- Structured handling of unknown tools.
- Validation and execution error reporting.
- Recovery for eligible failures.
- Explicit handling of malformed actions, model errors, and execution limits.

### Benchmarking

- A dataset of 31 benchmark tasks.
- Baseline and recovery evaluation on the same tasks.
- Per-task execution records.
- Overall and per-category metrics.
- JSON persistence for experiment results and summaries.
- Protection against accidentally overwriting existing run files.
- Automated tests for benchmark execution and reporting.

## Architecture

The project separates agent behavior, tool execution, benchmark definitions, and evaluation.

```text
User Task
    |
    v
Agent
    |
    v
Mock Model
    |
    v
Action Validation
    |
    v
Tool Registry
    |
    v
Tool Execution
    |
    v
Structured Result
    |
    +----> Success
    |
    +----> Eligible Failure
                |
                v
        Bounded Recovery
                |
                v
        Retry or Terminate
```

The benchmark runner evaluates each task independently under both strategies. Each run receives a fresh mock model and tool registry, preventing the state of one strategy's execution from carrying over into the other.

Results are aggregated into a summary containing completion rates, execution steps, retry counts, status distributions, and comparisons between strategies.

## Project Structure

```text
AgentBench Lite/
├── agentbench/
│   ├── __init__.py
│   ├── agent.py
│   ├── benchmark.py
│   ├── benchmark_runner.py
│   ├── execution.py
│   ├── tools.py
│   └── validation.py
├── benchmarks/
│   └── tasks.py
├── experiments/
├── tests/
│   ├── test_agent.py
│   ├── test_benchmark.py
│   ├── test_benchmark_runner.py
│   ├── test_execution.py
│   ├── test_tools.py
│   └── test_validation.py
├── results/
│   ├── .gitkeep
│   └── benchmark result and summary JSON files
├── .gitignore
├── requirements.txt
└── README.md
```

### Core modules

| Module                           | Responsibility                                                                      |
| -------------------------------- | ----------------------------------------------------------------------------------- |
| `agentbench/agent.py`            | Agent loop, mock model, execution strategies, retry behavior, and terminal statuses |
| `agentbench/tools.py`            | Deterministic tool implementations                                                  |
| `agentbench/validation.py`       | Validation of tool actions and arguments                                            |
| `agentbench/execution.py`        | Tool registry, dispatch, execution, and structured tool results                     |
| `agentbench/benchmark.py`        | Benchmark task definitions, categories, and dataset validation                      |
| `agentbench/benchmark_runner.py` | Strategy evaluation, metric aggregation, and JSON persistence                       |
| `benchmarks/tasks.py`            | The 31-task benchmark dataset                                                       |
| `tests/`                         | Automated tests for the implementation                                              |

## Requirements

- Python 3.12 or a compatible Python version.
- `pip`.
- Git (recommended for version control).
- PowerShell on Windows for the commands below.

The project has been tested with Python 3.12.10 and pytest 9.1.1.

## Installation

Open PowerShell and navigate to the project directory:

```powershell
cd "C:\Users\sivap\OneDrive\Desktop\AgentBench Lite"
```

Create a virtual environment if you have not already created one:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the project's dependencies:

```powershell
python -m pip install -r requirements.txt
```

Verify the Python and pytest installations:

```powershell
python --version
python -m pytest --version
```

If the virtual environment already exists, activate it and continue with the remaining steps.

## Running the Tests

Run the complete test suite:

```powershell
python -m pytest -v
```

The current verified test suite contains **139 passing tests**.

Run tests for an individual component when debugging:

```powershell
python -m pytest tests/test_agent.py -v
python -m pytest tests/test_execution.py -v
python -m pytest tests/test_tools.py -v
python -m pytest tests/test_validation.py -v
python -m pytest tests/test_benchmark.py -v
python -m pytest tests/test_benchmark_runner.py -v
```

The tests cover agent behavior, tool execution, validation, retry logic, benchmark validation, metric calculations, result persistence, and overwrite protection.

## Running the Benchmark

From the project root, run:

```powershell
python -m agentbench.benchmark_runner
```

The benchmark runner evaluates the dataset in `benchmarks/tasks.py` under both baseline and recovery strategies.

For a successful run, it prints summary information and writes two JSON files into `results/`:

```text
results/
├── benchmark_results_<run_id>.json
└── benchmark_summary_<run_id>.json
```

The exact filenames depend on the generated run ID.

### Detailed results

The results JSON contains individual task-strategy records, including expected and actual statuses, expected and actual results, completion indicators, step counts, retry counts, and execution history.

### Summary results

The summary JSON contains aggregated metrics for both strategies, including:

- Total tasks and completed tasks.
- Completion rates.
- Terminal status counts.
- Status matches and mismatches.
- Total steps and retries.
- Average steps and retries per task.
- Per-category results.
- Differences between the two strategies.

### Important

The runner protects existing result files from accidental overwriting. Preserve experiment outputs so that earlier runs remain available for comparison.

## Benchmark Design

The benchmark contains **31 deterministic tasks** distributed across 12 represented categories.

| Category             | Purpose                                                       |
| -------------------- | ------------------------------------------------------------- |
| `tool_selection`     | Tests selection of an appropriate tool                        |
| `calculator`         | Tests arithmetic operations                                   |
| `unit_conversion`    | Tests supported unit conversions                              |
| `mock_lookup`        | Tests predefined information retrieval                        |
| `unknown_tool`       | Tests behavior when a requested tool does not exist           |
| `validation_failure` | Tests invalid or missing tool arguments                       |
| `execution_failure`  | Tests failures during tool execution                          |
| `malformed_action`   | Tests malformed model actions                                 |
| `model_failure`      | Tests model-interface failures                                |
| `recovery_success`   | Tests recovery from an eligible failure                       |
| `recovery_failure`   | Tests failures that remain unresolved after recovery          |
| `step_limit`         | Tests execution-step limits                                   |
| `retry_exhaustion`   | Tests cases where retry allowance is unavailable or exhausted |

The list contains 13 category names, but only 12 categories are represented in the current dataset. The benchmark category definitions also include `retry_exhaustion`; consult `benchmarks/tasks.py` for the exact task distribution.

The two strategies use the same task definitions and scripted action sequences. Strategy-specific expected statuses account for tasks that are deliberately designed to succeed only when recovery is enabled.

## Evaluation Metrics

### Completion rate

The proportion of tasks completed successfully under a strategy:

\[
\text{Completion Rate}
=
\frac{\text{Completed Tasks}}{\text{Total Tasks}}
\]

### Completion-rate difference

The change in completion rate from baseline to recovery:

\[
\Delta\_{\text{pp}}
=
(\text{Recovery Rate}-\text{Baseline Rate})\times100
\]

This difference is reported in percentage points.

### Execution steps

The total number of model decisions across all tasks. Retry decisions contribute to the step count.

### Additional retries

The difference between the total retries used by recovery and baseline.

### Status mismatches

The number of task runs where the actual terminal status differs from the strategy-specific expected status.

### Per-category performance

Completion and failure metrics are also reported by benchmark category to help identify which task types benefit from recovery and which remain difficult.

## Experimental Results

The verified benchmark run `20261021T162446Z` produced the following results.

| Metric                       | Baseline | Recovery |
| ---------------------------- | -------: | -------: |
| Tasks evaluated              |       31 |       31 |
| Completed tasks              |       15 |       18 |
| Failed or unsuccessful tasks |       16 |       13 |
| Completion rate              |   48.39% |   58.06% |
| Total execution steps        |       31 |       36 |
| Total corrective retries     |        0 |        5 |
| Status mismatches            |        0 |        0 |

### Interpretation

Recovery completed three more tasks than baseline, improving the completion rate by **9.68 percentage points**.

This improvement required five additional execution steps and five corrective retries. The results illustrate the trade-off between task completion and additional execution overhead.

The improvement is concentrated in the benchmark's recovery-oriented tasks. It does not imply that all categories improve or that every failure can be recovered from.

These results are an initial deterministic experiment, not a statistically generalizable evaluation of LLM-based agents. Further experiments with real models, more diverse tasks, and repeated trials are needed to assess broader reliability.

## Reproducibility

The current benchmark is designed to be deterministic:

- Tasks use scripted model actions.
- The default tools use deterministic behavior.
- Each task-strategy run receives a fresh model and registry.
- The same benchmark definitions are used for both strategies.
- Results and summaries are saved as JSON.

A reproducibility check can run the benchmark twice with distinct run IDs:

```powershell
python -c "from benchmarks.tasks import BENCHMARK_TASKS; from agentbench.benchmark_runner import run_benchmark; a=run_benchmark(BENCHMARK_TASKS, output_dir='results/repro_check', run_id='run_a'); b=run_benchmark(BENCHMARK_TASKS, output_dir='results/repro_check', run_id='run_b'); print('Records identical:', a['results'] == b['results']); print('Metrics identical:', a['summary'] == b['summary'])"
```

The verified output was:

```text
Records identical: True
Metrics identical: True
```

The comparison checks result records and summary metrics, rather than run-specific metadata such as timestamps and run IDs.

Keep the JSON artifacts with their corresponding code and benchmark definitions when documenting or sharing an experiment.

## Limitations

The current implementation has several important limitations:

1. **Scripted model behavior:** `MockModel` returns predefined actions. It does not represent the uncertainty or variability of a live LLM.
2. **Synthetic task distribution:** The 31 benchmark tasks provide a controlled initial dataset, not a comprehensive sample of real-world tool-use tasks.
3. **Limited tool environment:** The tools are local and deterministic. External APIs, network failures, authentication, and changing external data are not evaluated.
4. **Bounded recovery scope:** Only selected error types are eligible for corrective retry. Some failures are intentionally not retried.
5. **Limited statistical evidence:** The current results are not sufficient to establish statistical significance or broad generalization.
6. **Simplified overhead measurement:** Steps and retry counts are tracked, but real latency, token usage, API cost, and infrastructure overhead are not measured.
7. **No production-safety claim:** The benchmark is a research prototype and does not establish production readiness or safety for autonomous tool execution.

These limitations should be considered when interpreting results or comparing the project with other agent evaluation systems.

## Future Work

Potential next steps include:

- Integrating a real LLM through a configurable model interface.
- Expanding the benchmark with more diverse tool-use tasks.
- Adding repeated trials and statistical analysis.
- Measuring latency, token consumption, and monetary cost.
- Evaluating recovery under transient and persistent failures.
- Adding structured experiment configuration and metadata.
- Comparing alternative retry policies and recovery limits.
- Improving reporting and visualization of benchmark results.
- Documenting the experimental protocol and research findings.

## License

No license has been specified yet. Add a license before distributing or accepting external contributions if the project requires one.

---

**Project status:** The initial agent framework, deterministic tools, validation and execution modules, benchmark dataset, benchmark runner, JSON result persistence, and automated test suite are implemented. The current test suite has 139 passing tests, and the initial baseline-versus-recovery benchmark has been executed successfully.
