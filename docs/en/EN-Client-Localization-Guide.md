# Adapting the bot to the English (US/Global) client

This is the workflow for making recognition work on the English game client. It's
separate from the GUI translation (that's `interface*.json` + the `languages` map).

## The big picture

- The resource **"US Server (Dark Winter)"** = `base` + **`resource_en`**. MaaFramework
  merges them and any node redefined in `resource_en` **overrides** the same-named base
  node (FIELD-LEVEL merge — you only specify the fields you change). So all EN fixes go
  in `resource_en`; `base` (the Chinese client) is never touched.
- A node recognizes the screen one of two ways:
  - **OCR** (`recognition: "OCR"`, `expected: "<text>"`) — matches on-screen text. Fix by
    translating the text. `expected` is a **regex** (so `Skip`, `^Cancel$`, `A|B` all work).
  - **TemplateMatch** (`recognition: "TemplateMatch"`, `template: "<img>.png"`) — matches a
    cropped image. Fix by supplying an English-client crop, or replacing it with OCR / a
    fixed-coordinate click.

## The loop

### 1. Run the task. If it stalls, find the failing node
- `install/debug/maafw.log` → search for `Task timeout [pretask.name=NODE]` and
  `Node.Recognition.Failed`. That `NODE` is what's stuck. TemplateMatch lines show the
  best `score` (needs ~0.7); OCR lines show what text it read.
- `install/debug/on_error/<timestamp>_<NODE>.png` → MaaFramework auto-saves the **exact
  failing frame at 1280×720** (the reference resolution). Use it to read text, get click
  coordinates, or crop templates at the correct scale.

### 2. Locate the node in the base pipeline
- `assets/resource/base/pipeline/**/*.json` (these are **JSONC** — `//` comments allowed).
  Read the node's `recognition`, `expected`/`template`, `action`, `roi`, `next` to learn
  its intent (e.g. doc "进入拆解界面" = "enter dismantle page"; roi at the top = a tab).

### 3a. Fix an OCR text node (the easy, common case)
- Open `assets/resource_en_glossary.json`, find the Chinese string under `"ocr"`, and set
  its English value (read it off the EN client — don't translate literally; menu/nav names
  especially differ, e.g. 活动层 = "Crew Deck", not "Activity Floor").
- Regenerate: `python scripts/build_en_resource.py`
  - This writes all OCR overrides to `resource_en/pipeline/_auto_en_ocr.json`. One filled
    string can fix many nodes (common words are reused).

### 3b. Fix a template / special node (manual override)
- Add the node to a hand-written file under `assets/resource/resource_en/pipeline/`
  (mirror the base path, e.g. `public/活动层/美味烹调.json`). The generator SKIPS any node
  defined manually, so it won't fight you.
- Options:
  - **New EN template:** crop the element from the on_error frame (1280×720) with PIL into
    `resource_en/image/<dir>/<name>.png`, then `{"recognition":"TemplateMatch",
    "template":"<dir>/<name>.png","threshold":0.6,"roi":[...],"action":"Click"}`.
  - **OCR + fixed click:** `{"recognition":"OCR","expected":"<screen text>","action":"Click",
    "target":[x,y,w,h]}` (clicks the center of the target box; coords in 1280×720).

### 4. Rebuild and test
```powershell
$env:PYTHONUTF8=1
.\.venv\Scripts\python.exe install.py            # reassembles install\
# (config/ is wiped each rebuild; pick Settings -> Language -> English, or set
#  install\config\config.json  "CurrentLanguage":"en-US")
.\install\MaaGF2Exilium.exe
```

## Worked example: the cooking flow (`美味烹调`)

Base file: `assets/resource/base/pipeline/public/活动层/美味烹调.json`. Node order:

1. `进入活动层-美味烹调` — OCR, click **"Crew Deck"** (zh 活动层) to enter the floor
2. `走向美味烹调` — swipe toward the cooking station
3. `进入美味烹调区域` — OCR, click **"Delicious Cuisine"** (zh 美味烹调)
4. `每天第一次免费美味烹调` — OCR **"each day is free"** (zh 每日首次免费)
5. `选择常规菜品` — pick a dish *(override: OCR "Select Dish" + click first dish)*
6. `邀请人形-美味烹调` — OCR, click **"Next"** (zh 下一步)
7. `确认邀请-美味烹调` — OCR, click **"Confirm Invite"** (zh 确认邀请)
8. `跳过动画-美味烹调` — skip the cutscene *(override: TemplateMatch the "Skip" button)*
9. `确认结果-美味烹调` — OCR, click **"Confirm"** (zh 确认)
10. `退出活动层-美味烹调` — exit (TemplateMatch the exit button)
11. `美味烹调任务结束` — OCR **"Campaign"** = done (zh 战役推进)

Overrides for steps 5 & 8 live in
`assets/resource/resource_en/pipeline/public/活动层/美味烹调.json` — read them as templates
for your own fixes.

## Rules of thumb
- Never edit `base/` for EN fixes — only `resource_en/`.
- Identifiers (node names, option keys) stay Chinese; you only change `expected`/`template`.
- Verify wording against the actual EN screen (on_error frame), don't translate literally.
- After any change: `python scripts/build_en_resource.py` (if you touched the glossary) then
  `python install.py`.
