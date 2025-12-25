# Title Genie - Windows EXE Build Instructions (打包指南)

由于开发环境是 macOS，无法直接生成 Windows `.exe` 文件。请在 **Windows 电脑** 上按照以下步骤打包。

## 1. 准备环境 (Prerequisites)
1.  安装 Python (建议 3.10 或 3.11): [下载 Python](https://www.python.org/downloads/windows/)
2.  下载本项目代码到 Windows 电脑。

## 2. 安装依赖 (Install Dependencies)
打开 CMD 或 PowerShell，进入项目目录，运行：

```bash
pip install -r requirements.txt
pip install pyinstaller
```

## 3. 开始打包 (Build)
在项目根目录下，运行以下命令：

```bash
# 生成 .spec 文件 (配置打包规则)
# 注意：你需要手动创建一个 hooks 文件夹或者直接使用以下命令生成基础 spec
pyinstaller --name TitleGenie --onefile --additional-hooks-dir=. launcher.py
```

### 推荐使用的完整打包命令 (One-Liner)
为了确保 `app.py`, `utils` 和 `assets` 都包含在内，请使用以下命令（复制并执行）：

```bash
pyinstaller --noconfirm --onefile --windowed --name "TitleGenie" ^
 --add-data "app.py;." ^
 --add-data "utils;utils" ^
 --add-data ".env.example;." ^
 --hidden-import "openpyxl" ^
 --hidden-import "pandas" ^
 --hidden-import "dashscope" ^
 launcher.py
```
*(注意：`^` 是 Windows 命令行的换行符。如果在 PowerShell 运行，请把 `^` 换成 `` ` `` 或者写成一行)*

**PowerShell 版本指令:**
```powershell
pyinstaller --noconfirm --onefile --windowed --name "TitleGenie" `
 --add-data "app.py;." `
 --add-data "utils;utils" `
 --add-data ".env.example;." `
 --hidden-import "openpyxl" `
 --hidden-import "pandas" `
 --hidden-import "dashscope" `
 launcher.py
```

## 4. 运行软件 (Run)
1.  打包成功后，在 `dist/` 文件夹中会生成 `TitleGenie.exe`。
2.  双击运行即可。初始化可能需要 10-20 秒。
3.  **注意**: 软件是基于浏览器的应用，启动后会自动打开默认浏览器显示操作界面。

## 常见问题 (FAQ)
*   **黑框闪过**: 如果启动失败，尝试去掉 `--windowed` 参数重新打包，这样可以看到报错信息。
*   **找不到文件**: 确保 `.env` 文件（如果有）放在 `TitleGenie.exe` 同级目录下。
