# 开发心得(给自己看的)
## 任务的自我调用
当一个任务被识别到但是可能因为动画效果点击后无反应，或者需要等待动画结束（很短的动画）。如果这个任务next中有下一个任务则可能会被影响，此时可以在next中调用自身，确保动作会反复执行，直到动作真的生效。

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

上述任务中，任务进入后提前判断到了点击空白处关闭，但是因为动画未结束所以动作无效，会导致`returnToHomePage`任务在无法预期情况下执行。可以在`returnToHomePage`前调用`closeClaimAllEmailsPopup`本身，直到无法识别到“点击空白处关闭”后失败，转向执行`closeClaimAllEmailsPopup`。

## 出现很少的弹窗或每周结算页面

这种页面要在上一个任务的next列表第一个来判断，使用is_sub循环识别，直到消失后返回到正常流程。
