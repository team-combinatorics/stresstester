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

### 安装依赖

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
# 根据.gitignore生成清理文件
py setup.py clean
# 打包运行环境
py setup.py build
# 生成压缩包
py setup.py pack
```

## 帮助文档

static文件夹下的文件会直接打包到安装包中，你可以直接修改、添加这些帮助文档。

目前只有一个`请先读我README.txt`文件，用于基本操作说明。

## 配置

测试配置文件为`config.ini`，位于项目根目录下。config.ini可以修改以下运行参数：

```ini
[stress]
;是否开启烤机
stress = True
;是否开启CPU烤机
stress_cpu = True
;CPU烤机后端，可选prime95或aida64
cpu_backend = aida64
;是否开启GPU烤机
stress_gpu = True
;GPU烤机后端，可选furmark或aida64
gpu_backend = furmark
;烤机时长，单位为分钟
stress_minutes = 20
;是否冷却
cooldown = True
;冷却时长，单位为分钟
cooldown_minutes = 5
;使用CPUZ跑分
cpuz_score = True
```

在程序加载时，会自动读取配置文件，如果配置文件不存在或配置文件有误，会使用程序中编码的默认配置。

