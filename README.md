# Tools
面向本地游戏/网络游戏/视觉小说的工具集

## 目录总览
- `_ThirdParty`：第三方依赖源码或脚本集合。
- `LocalGame`：本地/单机游戏相关工具与脚本。
- `OnlineGame`：网络/在线游戏相关工具，按引擎与具体游戏分类。
- `VisualNovel`：视觉小说相关工具。
- `Other`：杂项与通用脚本。

## 安装
1. 安装 uv
   - Windows：
     ```bash
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - macOS and Linux：
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
2. 同步依赖：
   ```bash
   uv sync
   ```
3. 激活虚拟环境：
   ```bash
   .\.venv\Scripts\activate
   ```

## 致谢与来源
- 本仓库集成/参考/重写了多项开源工具及项目：
  - Wwise/CRI 相关解析器、Lua 反汇编、FreeMote、各游戏社区工具等（见各子目录 README 的 Reference 链接）。
- 具体出处与协议请见对应子目录与文件顶部注释/README。

## 免责声明
- 本项目仅用于技术研究与学习，请遵守目标游戏与资源的使用条款及所在地区法律法规。
- 任何因使用本工具造成的后果由使用者自行承担；请勿将相关成果用于商业或侵权用途。