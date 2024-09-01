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

0. 默认用户的操作系统为 Windows 系统(其他操作系统未测试过)。
1. 推荐使用MuMu模拟器12运行游戏，[模拟器支持情况](https://maa.plus/docs/zh-cn/manual/device/windows.html)请查看官方文档。
2. 模拟器建议设置为`16:9`的比例的分辨率，该比例典型的分辨率有`3840*2160 (4K)`、`2560*1440 (2K)`、`1920*1080 (1080P)`、`1280*720 (720P)`。

## 使用方式

 > 现已发布测试版，下载测试版之后即可使用

 0. 从 [Releases](https://github.com/DarkLingYun/MaaGF2Exilium/releases)下载压缩包名为 `MaaGF2Exilium-win-x86_64-with-gui-v0.x.x.zip
` 的GUI版本。
 1. 解压下载好的压缩包
 2. 双击或右键运行解压目录下的 `MFAWPF.exe` 文件即可 **(确保[MuMu模拟器](https://mumu.163.com/)已运行)**

## 已有功能
> 定向精研（武器配件刷取）由于逻辑比较复杂，写到自律补给作战里面作为选项比较麻烦，因此单独写成一个功能供用户使用。
> 
> 一般而言自律补给作战和定向精研的任务二选一即可，因为这两个任务都默认会消耗完全部体力，如果两个都选了，由于第一个任务已经消耗完了体力，第二个任务只会在体力耗尽的情况下白执行一遍。
* [x] 启动游戏

* [x] 日常任务前准备
  * [x] 领取邮件
  * [x] 使用完体力药水
  * [x] 商城购买每日免费补给箱

* [x] 公共区日常
  * [x] 访问休息室
  * [x] 调度室任务一键领取和再次派遣
  * [ ] 领取调度收益的情报储备和资源生产
  * [ ] 派遣收益领取

* [x] 实兵演习[即将废弃]

* [x] 定向精研[三选一]
  * [x] 支持配件类型与配件效果选择
  * [x] 自动寻找最高可自律关卡(玩家需要确保每个配件类型下至少有一个可自律关卡) 

* [x] 补给作战[三选一]
  * [x] 自动寻找最高可自律关卡(玩家需要确保至少有一个可自律关卡) 
  * [ ] 补给资源选择：
    * [x] 战争报告_人形升级
    * [x] 解析图纸_武器升级
    * [x] 增域存量条_提升人形等级上限
    * [ ] 萨狄斯金_配件精调及心智螺旋(八成是懒得做了)
* [x] 心智勘测[三选一]
  * [x] 材料选择
  * [x] 自动寻找最高可自律关卡

* [x] 模拟作战日常
  * [x] 常规首领挑战自律
    * [ ] 暂不支持自律，等下周更新
    * [ ] 讯段交易
  * [x] 自动实兵演习
  * [x] 自动兵棋推演
    - 暂不支持自动领取推演奖励

* [ ] 班组日常
  * [ ] 补给领取
  * [ ] 要务自动战斗
  * [ ] 尘烟前线自动作战
  * [ ] 尘烟前线补给领取
  * [ ] 班组商店自动购物
  * [ ] 班组商店优先性选择

* [x] 人形常规招募(抽到新装备还未测试,未来可能取消此功能) 
    - 支持选择访问方式为单抽还是十连，直到访问资源不足为止

* [x] 领取活动页奖励及物品
  * [x] 日行迹领取
  * [x] 彻夜疾行领取
  * [x] ~~领取体力~~(有此活动时更新)

* [x] 每日任务一键领取

* [x] 通行证领取
  * [ ] 通行证奖励箱子领取内容确认


## 开发相关
### 致谢

- [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 自动化测试框架

- [MaaPracticeBoilerplate](https://github.com/MaaXYZ/MaaPracticeBoilerplate) MaaFramework项目模板

- [MFAWPF](https://github.com/SweetSmellFox/MFAWPF) Pipeline协议项目的通用GUI
- [MFATools](https://github.com/SweetSmellFox/MFATools) 开发工具
- [maa-support-extension](https://github.com/neko-para/maa-support-extension) VSCode扩展
### 规范
> 如果要参与开发，请查看以下规范文档。方便更好的开发和管理。

- [Json规划说明](/docs/Json文件说明.md)
- [Git提交前缀](/docs/Git提交前缀.md)  ~~给自己看的~~

## 鸣谢

本项目由 **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)** 强力驱动！

感谢以下开发者对本作出的贡献:

<a href="https://github.com/DarkLingYun/MaaGF2Exilium/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=DarkLingYun/MaaGF2Exilium" />
</a>

Made with [contrib.rocks](https://contrib.rocks)
