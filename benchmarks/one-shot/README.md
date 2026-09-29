# One-shot artifact tasks

This suite compares agents on a fixed prompt with no follow-up clarification. Every task definition records the prompt, requested artifact, run limits, capability requirements, and evaluator type. Every final response must include a run receipt following [the response contract](response-contract.md). Preserve generated artifacts for audit.

| ID | Artifact | Evaluation |
|---|---|---|
| `oneshot.ascii-mona-lisa.v1` | ASCII rendering | Exact output checks plus image-to-glyph similarity |
| `oneshot.image-mona-lisa.v1` | Image | Validity and perceptual / blinded human scoring |
| `oneshot.video-mona-lisa.v1` | Short video | Encoding, duration, frame sampling, temporal and human scoring |
| `oneshot.xlsx-sales-report.v1` | Excel workbook | Cell, formula, type, sheet, and formatting assertions |

Do not combine capability-mismatched results into the same leaderboard. A text-only agent and an agent with image generation can appear in separate capability tracks, with their available tools stated on every result.
