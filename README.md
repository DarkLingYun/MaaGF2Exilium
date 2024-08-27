<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <img alt="LOGO" src="https://cdn.jsdelivr.net/gh/MaaAssistantArknights/design@main/logo/maa-logo_512x512.png" width="256" height="256" />
</p>

<div align="center">

# MaaGF2Exilium助手

</div>

本项目基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 所提供的项目模板进行开发的少女前线2：追放的自动化助手。

> **MaaFramework** 是基于图像识别技术、运用 [MAA](https://github.com/MaaAssistantArknights/MaaAssistantArknights) 开发经验去芜存菁、完全重写的新一代自动化黑盒测试框架。
> 低代码的同时仍拥有高扩展性，旨在打造一款丰富、领先、且实用的开源库，助力开发者轻松编写出更好的黑盒测试程序，并推广普及。
## 联系方式
如果有不懂的地方，抑或是想要添加的功能，或者你也想一起开发，甚至是划水聊天~~催更~~。欢迎加入交流QQ群：904823072。
## 使用前提
0. 默认用户使用 Windows 系统运行。
1. 推荐使用MuMu模拟器12运行游戏，[模拟器支持情况](https://maa.plus/docs/zh-cn/manual/device/windows.html)请查看官方文档。
2. 模拟器建议设置为`16:9`的比例的分辨率，该比例典型的分辨率有`3840*2160 (4K)`、`2560*1440 (2K)`、`1920*1080 (1080P)`、`1280*720 (720P)`。
## 使用方式
 > 暂不打算发版，等所有功能稳定后再进行发版。因此如果想要现在使用，请先按照下列方式使用。
 0. 确保电脑已经安装了 Python 环境。
 1. 克隆完整本项目及子项目。
    ```git
    git clone --recursive https://github.com/DarkLingYun/MaaGF2Exilium.git
    ```
  2. 下载 MaaFramework 的 [Release](https://github.com/MaaXYZ/MaaFramework/releases) 包，解压到 deps 文件夹中。
  3. 运行项目文件下的 `install.bat` 文件，编译项目。
  4. 运行模拟器其后，运行编译后生成的 install 文件夹下的 `MaaPiCli.exe` 文件。
  5. `Select controller ` 选择模式，选择`1. 安卓端`，输入`1` 回车。

      ```cmd
      ### Select controller ###

              1. 安卓端
              2. 桌面端

      Please input [1-2]: 1
      ```

  6. `Select ADB` 选择 ADB 连接地址，选择`1. Auto detect`,输入`1` 回车自动搜索（前提是打开模拟器），之后弹出自动搜索到的链接地址,选择对应的地址后回车。

      ```cmd
      ### Select ADB ###

        1. Auto detect
        2. Manual input

      Please input [1-2]: 1

      Finding device...

      ## Select Device ##

              1. MuMuPlayer12
                      C:/Game/MuMu Player 12/shell/adb.exe
                      127.0.0.1:16384

      Please input [1-1]: 1
      ```

  7. `Add task` 添加任务列表，输入对应的任务列表。推荐按照示例添加。若添加了带有选项的任务，则会提示设置选项,之后回车即可。
      
      ```cmd
      ### Add task ###

              1. 启动少女前线2
              2. 调度室每日任务
              3. 领取邮件
              4. 领取活动奖励
              5. 使用完体力药水
              6. 进入休息室
              7. 实兵演习
              8. ————————————下列二选一————————————
              9. 定向精研（武器配件刷取）
              10. 自律补给作战
              11. ——————————————————————————————
              12. 人形常规招募(抽到新装备还未测试)
              13. 每日任务一键领取
              14. 通行证领取

      Please input multiple [1-14]: 1 2 3 5 6 7 9 4 13 14



      ## Input option of "配件类型：" for "定向精研（武器配件刷取）" ##

              1. 突击与霰弹枪
              2. 冲锋枪与机枪
              3. 狙击枪与刀
              4. 手枪

      Please input [1-4]: 1



      ## Input option of "配件效果：" for "定向精研（武器配件刷取）" ##

              1. 制胜追进
              2. 双重对策
              3. 异位打击
              4. 异位提振
              5. 应急修复
              6. 减伤支援
              7. 实弹增幅
              8. 炙热增幅
              9. 冰点增幅
              10. 强蚀增幅
              11. 电场增幅
              12. 激流增幅

      Please input [1-12]: 10
      ```

  8. 到这一步之后，输入`6`选择运行即可开始运行脚本。之后每次打开都是从这里开始，无需再次配置。如需要修改，按照菜单修改即可（菜单英文应该不需要我翻译了吧）。
        
        ```cmd
        Welcome to use Maa Project Interface CLI!
        MaaFramework: v1.8.8

        Version: v0.0.1

        ### Current configuration ###

        Controller:

                安卓端
                        C:/Game/MuMu Player 12/shell/adb.exe
                        127.0.0.1:16384

        Resource:

                官服

        Tasks:

                - 启动少女前线2
                - 调度室每日任务
                - 领取邮件
                - 使用完体力药水
                - 进入休息室
                - 实兵演习
                - 定向精研（武器配件刷取）
                        - 配件类型：: 突击与霰弹枪
                        - 配件效果：: 强蚀增幅
                - 领取活动奖励
                - 每日任务一键领取
                - 通行证领取

        ### Select action ###

                1. Switch controller
                2. Switch resource
                3. Add task
                4. Move task
                5. Delete task
                6. Run tasks
                7. Exit

        Please input [1-7]: 6
        ```
## 已有功能
> 定向精研（武器配件刷取）由于逻辑比较复杂，写到自律补给作战里面作为选项比较麻烦，因此单独写成一个功能供用户使用。
> 
> 一般而言自律补给作战和定向精研的任务二选一即可，因为这两个任务都默认会消耗完全部体力，如果两个都选了，由于第一个任务已经消耗完了体力，第二个任务只会在体力耗尽的情况下白执行一遍。
* [x] 启动游戏
* [x] 调度室功能
  * [x] 调度室派遣
  * [ ] 调度室领取溢出体力
* [x] 领取邮件
* [x] 领取活动页奖励及物品
  * [x] 日行踪领取
  * [x] 彻夜疾行领取
  * [x] ~~领取体力~~
* [x] 使用完体力药水
* [x] 进入休息室
* [x] 实兵演习
* [x] 定向精研（武器配件刷取）
* [x] 自律补给作战（通用）
    * [ ] 补给资源选择：
        * [x] 战争报告_人形升级
        * [x] 解析图纸_武器升级
        * [x] 增域存量条_提升人形等级上限
        * [ ] 萨狄斯金_配件精调及心智螺旋
* [x] 人形常规招募(抽到新装备还未测试,未来可能取消此功能) 
    - 支持选择访问方式为单抽还是十连，直到访问资源不足为止
* [x] 每日任务一键领取
* [x] 通行证领取

## 鸣谢

本项目由 **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)** 强力驱动！

感谢以下开发者对本作出的贡献:

<a href="https://github.com/DarkLingYun/MaaGF2Exilium/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=DarkLingYun/MaaGF2Exilium" />
</a>

Made with [contrib.rocks](https://contrib.rocks)