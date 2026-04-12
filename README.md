# ray-game

一个使用 `uv` 管理的 Python + raylib + raygui 示例项目。

## 功能

- 中文字体默认从项目根目录的 `./font.ttf` 读取
- 程序会按中文字库范围一次性加载字形，新增一般中文文案通常不用额外改字符列表

## 运行

```bash
uv sync
uv run ray-game
```

## Web 打包

```bash
make web
make web-serve
make web-package
```

然后打开 `http://localhost:8000/`。

说明：

- Web 打包不会再直接扫描整个仓库，而是先组装一个最小 staging 目录再交给 `pygbag`
- 这样可以避免把 `.venv`、本机 `.so`、构建缓存和设计文档误打进 Web 包里
- 当前 Web 包会包含 `main.py`、`font.ttf` 和 `src/raygame`
- itch.io 最终上传包会生成到 `build/ray-game-itch.zip`

## 环境

- Python 3.13
- `raylib==5.5.0.3`
- 把中文字体文件命名为 `font.ttf` 放到项目根目录下
- Web 版使用 `pygbag`，运行入口仍然是 `main.py`
