Convert inputs/portrait.pgm to ASCII art and write submission/art.txt as UTF-8. Use this exact ramp from darkest to lightest: @%#*+=-:. (space). Map each pixel with index = min(9, pixel * 9 // (maximum + 1)); preserve image width and height, trimming trailing spaces on each line. No title, Markdown fences, or commentary in art.txt.

## Fixed task package

Read every file listed in `context_files` in `task.json`. The same package includes all task inputs and any starter files. Work from the task workspace, use relative paths, and write deliverables under `submission/`.
