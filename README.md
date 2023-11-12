# 电脑小队系统测试工具

## 环境搭建

### 安装Python

因为[Asyncio在Windows上的兼容性问题](https://github.com/python/cpython/issues/88050)，这个工具需要Python 3.11.2或更高版本。
你可以从[Python官网](https://www.python.org/downloads/)下载Python。

### Virtualenv

我们建议使用venv来安装Python依赖项。它可以创建一个独立的Python环境，这样你就可以在不影响其他项目的情况下安装Python包。

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
# 清理文件
py setup.py clean
# 打包
py setup.py build
# 生成压缩包
py setup.py pack
```

## 编辑文档

static文件夹下的文件会直接打包到安装包中，可以直接修改。
目前只有一个README读我.txt文件，用于安装包的说明。

