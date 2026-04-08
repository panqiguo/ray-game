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
```

然后打开 `localhost:8000`。

## 环境

- Python 3.13
- `raylib==5.5.0.3`
- 把中文字体文件命名为 `font.ttf` 放到项目根目录下
- Web 版使用 `pygbag`，入口是项目根目录的 `main.py`
