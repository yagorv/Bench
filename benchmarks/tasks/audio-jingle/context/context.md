# Audio generation contract

Create an original eight-second electronic jingle from the fixed score in `inputs/score.json`. Use one equal-tempered sine note at a time, in the listed order, with no accompaniment or effects. Every note lasts exactly `note_seconds`; the tempo is 120 BPM. Use a short 5 ms fade at each note edge to avoid clicks. Write mono, signed 16-bit PCM WAV at the score's sample rate to `submission/jingle.wav`.

This task has two review layers. The local evaluator checks WAV format, exact duration, audible output, and the pitch of every note. The benchmark owner should also listen to the saved jingle and judge whether it sounds clean and follows the score. The HTML review gallery embeds an audio player for this file.
