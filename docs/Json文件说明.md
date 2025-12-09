# JSON说明
项目是基于[任务流水线（Pipeline）协议](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/3.1-%E4%BB%BB%E5%8A%A1%E6%B5%81%E6%B0%B4%E7%BA%BF%E5%8D%8F%E8%AE%AE.md)编写的，因此为了更好的管理JSON文件，对文件命名和文件位置和做了一些规范。

## JSON文件命名规范
> 规范只是让其更好的管理文件，并非一定要遵守。
1. 作为任务入口（被interface.json文件调用）的JSON文件，命名为大驼峰命名法，即每个单词都大写,例： `LoungeTasks.json` ，该文件一般被放入 `assets\resource\base\pipeline\tasks` 目录下。
2. 被其他JSON文件调用，不直接写入interface.Json文件的。以小驼峰命名法命名，即第一个单词以小写字母开头，其余单词开头大写，例：`battleTask.json` ，该类型文件一般被放入 `assets\resource\base\pipeline\public` 文件夹中。
3. 为了兼容未来版本，尽量减少属性字段 `is_sub` 的使用 

## JSON文件位置
可编辑的大部分任务JSON文件位置都位于项目目录下的 `assets/resource/base/pipeline` 的子目录中，目录结构如下。

  ```cmd
  base
    ├─image
    │  ├─公用按钮组件
    │  ├─实兵演习
    │  ├─招募
    │  └─整备室
    ├─model
    │  └─ocr
    └─pipeline
        ├─public
        ├─tasks
        ├─timeLimitedTasks
        └─test
  ```

- `public` 目录，用于存放被其他JSON调用，即任务入口文件调用的JSON文件，文件名和任务名均采用小驼峰命名法。
- `tasks` 目录，存放任务入口JSON文件，被`assets\interface.json`文件调用，文件名和任务入口一致且采用大驼峰命名法。
- `timeLimitedTasks` 目录，存放具有时效性的任务入口JSON文件，例如：活动页面领取体力、限时活动奖励、版本活动关卡。被`assets\interface.json`文件调用 ，文件名和任务入口名规范同上。
- `test` 目录，用于存放正在编写、未完成、或者测试的JSON文件。

## PC端使用的CheckKey相关信息

[Maa教程对应地址](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/3.1-%E4%BB%BB%E5%8A%A1%E6%B5%81%E6%B0%B4%E7%BA%BF%E5%8D%8F%E8%AE%AE.md#clickkey)

**按键对照表**：[微软官方网址](https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes)
