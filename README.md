# 电脑小队系统测试工具

## 环境搭建

### 安装Python

这个工具需要Python 3.11.2或更高版本。[Asyncio Termination Issue](https://github.com/python/cpython/issues/88050)

你可以从[Python官网](https://www.python.org/downloads/)下载Python。

### Virtualenv

我们建议使用Virtualenv来安装Python依赖项。Virtualenv是一个工具，可以创建一个独立的Python环境，这样你就可以在不影响其他项目的情况下安装Python包。

你可以使用以下命令安装Virtualenv：

```bash
pip install virtualenv
```

创建虚拟环境：

```bash
py -m venv venv
venv\Scripts\activate
```

### 安装依赖项

在项目根目录下，运行以下命令来安装依赖项：

```bash
pip install -r requirements.txt
```

## 运行

在项目根目录下，运行以下命令来运行测试工具：

```bash
py entrypoint.py
```

## 打包安装包

在项目根目录下，运行以下命令来打包安装包：

```bash
py setup.py build
```