# Development Guide

> English translation of [`docs/开发相关.md`](../开发相关.md).

## How to build locally

1. Clone the repo with `git clone --recurse-submodules https://github.com/xxx/xxx.git` to make sure submodules are included.
2. Install dependencies: a `pyproject.toml` and `requirements.txt` are provided. Use conda, uv, or any tool you like to install them.
3. Run `scripts/download_deps.py` to download the dependencies (MaaFramework + the MFAAvalonia GUI).
4. Run `install.py` to build.
5. The built output is the `install` folder.
6. To rebuild, just run step 4 again.

## Test accounts

There are currently shared test accounts: 2 on the CN official server and 1 on the US server.

If your own account isn't enough and you need a test account, join the QQ group and contact an admin.

## Tips

1. Avoid hard-coded click loops. Different emulators respond at different speeds; in a tight loop you may click a point from the previous screen onto the next screen.
2. If recognition keeps failing, try shrinking the ROI to reduce background interference.
3. Under default settings, `FeatureMatch` is not necessarily better at recognition than `TemplateMatch`.

## Visualizing pipeline logic

You can use a small tool to turn a pipeline into Mermaid code and visualize the execution flow:

1. In `scripts/json_to_mermaid.py`, set `json_file` to the path of the target file. On Windows, keep the leading `r` so the path isn't escaped.
   Example: `json_file = r"assets\resource\pipeline\public\SimulatedCombat\liveDrillCombatLogic.json"`
   You can use your editor's "copy file path" feature.
2. Run `scripts/json_to_mermaid.py`.
3. Find the generated code in `mermaid.mmd` at the project root.
4. Use a locally hosted Mermaid renderer or https://mermaid.live/.
5. On mermaid.live, if the text looks too small, enable **Pan & Zoom**.

## Acknowledgements

- [MaaFramework](https://github.com/MaaXYZ/MaaFramework) — automation testing framework
- [MaaPracticeBoilerplate](https://github.com/MaaXYZ/MaaPracticeBoilerplate) — MaaFramework project template
- [MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia) — general-purpose GUI for Pipeline-protocol projects
- [MFATools](https://github.com/SweetSmellFox/MFATools) — development tools
- [maa-support-extension](https://github.com/neko-para/maa-support-extension) — VSCode extension

## Conventions

> If you want to contribute, please read the following convention docs first — they make development and maintenance smoother.

- [JSON file guide](JSON-Guide.md)
- [Git commit prefixes](Git-Commit-Prefixes.md)
