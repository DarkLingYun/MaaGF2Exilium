# Pipeline Development Notes

> English translation of [`docs/Pip协议心得.md`](../Pip协议心得.md). (Originally "notes to self".)

## A task calling itself

Sometimes a task is recognized but a click has no effect — maybe because of an animation, or because you need to wait for a (short) animation to finish. If that task has a follow-up in its `next`, the follow-up can be affected. In that case you can call the task itself in `next` so the action repeats until it actually takes effect.

```json
{
    "closeClaimAllEmailsPopup": {
    "recognition": "OCR",
    "expected": "点击空白处关闭",
    "action": "Click",
    "next": [
        "closeClaimAllEmailsPopup",
        "returnToHomePage"
    ]
}
```

In the task above, "tap a blank area to close" is detected early, but because the animation hasn't finished the click is ineffective — which causes `returnToHomePage` to run at an unexpected moment. By calling `closeClaimAllEmailsPopup` itself before `returnToHomePage`, it keeps retrying until "tap a blank area to close" can no longer be recognized (i.e. it fails), and then moves on.

## Rare popups or the weekly settlement page

Pages like these should be checked as the **first** item in the previous task's `next` list. Use `is_sub` to loop recognition until they disappear, then return to the normal flow.
