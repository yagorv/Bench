Generate the original eight-second jingle specified in `context/context.md` and `inputs/score.json`. Save a mono 16-bit PCM WAV at the specified sample rate as `submission/jingle.wav`. Follow the MIDI note sequence exactly, in order, for 0.5 seconds per note. Make the tone audible and clean, with a 5 ms fade at note boundaries. Do not substitute a description or a link for the audio file.

## Fixed task package

Read every file listed in `context_files` in `task.json`. Work from this task workspace, use relative paths, and write deliverables under `submission/`.

## Required usage receipt

Report only usage and cost you can actually inspect. Never estimate a billed cost. Write `submission/run-receipt.json` and include the identical JSON in your final response under `BENCHMARK_RUN_RECEIPT`. Use `null` for unavailable values and explain each unavailable value. Use this exact task ID:

```json
{
  "schema_version": 1,
  "task_id": "oneshot.audio-jingle.v1",
  "status": "completed",
  "agent_reported": {
    "model": null,
    "input_tokens": null,
    "output_tokens": null,
    "cached_input_tokens": null,
    "model_calls": null,
    "tool_calls": null,
    "wall_time_ms": null,
    "cost": null,
    "cost_currency": null,
    "cost_basis": "unknown"
  },
  "unavailable_fields": [
    {"field": "cost", "reason": "Not exposed to this tool or session"}
  ]
}
```

`status` may be `completed`, `partial`, `failed`, or `timed_out`. `cost_basis` may be `provider_reported`, `rate_card_estimate`, `subscription`, or `unknown`.
