# JSON Guide

> English translation of [`docs/Json文件说明.md`](../Json文件说明.md).

This project is written against the [Pipeline task protocol](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/en_us/3.1-PipelineProtocol.md). To keep the JSON files manageable, some conventions for file naming and location are followed.

## JSON file naming conventions

> These conventions just make files easier to manage; they aren't strictly mandatory.

1. A JSON file that serves as a **task entry** (called from `interface.json`) is named in **PascalCase** (every word capitalized), e.g. `LoungeTasks.json`. These files generally go under `assets\resource\base\pipeline\tasks`.
2. A JSON file that is **called by other JSON files** and not written directly into `interface.json` is named in **camelCase** (first word lowercase, the rest capitalized), e.g. `battleTask.json`. These files generally go under `assets\resource\base\pipeline\public`.
3. To stay compatible with future versions, minimize use of the `is_sub` attribute.

## JSON file locations

Most editable task JSON files live in subdirectories of `assets/resource/base/pipeline`. The directory layout:

```cmd
base
  ├─image
  │  ├─公用按钮组件   (shared button components)
  │  ├─实兵演习       (live drill)
  │  ├─招募           (recruitment)
  │  └─整备室         (prep room)
  ├─model
  │  └─ocr
  └─pipeline
      ├─public
      ├─tasks
      ├─timeLimitedTasks
      └─test
```

- `public` — holds JSON files called by other JSON files (i.e. called by task-entry files). File names and task names use camelCase.
- `tasks` — holds task-entry JSON files called by `assets\interface.json`. File names match the task entry and use PascalCase.
- `timeLimitedTasks` — holds time-limited task-entry JSON files (e.g. claiming stamina on an event page, limited-time event rewards, version event stages). Called by `assets\interface.json`; same naming rules as above.
- `test` — holds JSON files that are in progress, unfinished, or under test.

## CheckKey info for the PC client

[Corresponding MAA tutorial](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/en_us/3.1-PipelineProtocol.md#clickkey)

**Key reference table:** [Microsoft official page](https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes)
