Generate one specific 8-second, 16:9 video at 640x360 and 24 fps. Use a fixed camera and a plain white background. Show one solid red ball (about 72 pixels in diameter) at vertical center. Follow this timeline: 0–1s, ball still at x=72; 1–3s, move smoothly to x=256; 3–4s, bounce once in place, rising about 70 pixels and returning; 4–6s, move smoothly to x=568; 6–7s, hold still; 7–8s, fade the ball to white. Keep the whole ball inside frame. Save exactly `submission/video.mp4`.

The automatic check only validates MP4 container structure. Review the video yourself in the local artifact gallery for the requested timing, movement, dimensions, and visual glitches; these content checks are not included in the automatic score.

## Fixed task package

Read every file listed in `context_files` in `task.json`. The same package includes all task inputs and any starter files. Work from the task workspace, use relative paths, and write deliverables under `submission/`.

## Required usage receipt

Report only usage and cost you can actually inspect. Never estimate a billed cost. Write a JSON file at `submission/run-receipt.json` and include the identical JSON in your final response under the label `BENCHMARK_RUN_RECEIPT`. Use `null` for unavailable values and explain each unavailable value. Use the exact task ID shown below:

```json
{
  "schema_version": 1,
  "task_id": "oneshot.mp4-artifact.v1",
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

`status` may be `completed`, `partial`, `failed`, or `timed_out`. `cost_basis` may be `provider_reported`, `rate_card_estimate`, `subscription`, or `unknown`. Keep provider usage distinct from an agent estimate.
