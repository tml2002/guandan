# 惯蛋游戏可视化

这是一个基于tkinter的应用程序，用于使用JSON文件中的数据可视化惯蛋牌局的回合。

## 系统要求
- tkinter库
- customtkinter库（用于改进的UI元素）
- PIL库（用于图像处理）

## 安装
确保系统上已安装Python 3。你可能需要使用pip安装所需的库：

```bash
pip install customtkinter pillow

## 自定义
要自定义可视化工具，请修改脚本中的路径、文件名或UI元素。

## 注意
- 确保JSON数据文件和图像资源正确放置并命名。
- 脚本在回合之间使用1秒的延迟进行可视化。更改`update_rounds`函数中的`time.sleep(1)`以调整此设置。

## 运行
```bash
python TOM3,py
