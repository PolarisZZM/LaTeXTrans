<div align="center">

[English](README.md) | 中文 | [日本語](README_JP.md)

</div>

# 🚀 LaTeXTrans

> **基于多智能体协作的结构化LaTeX文档翻译系统**

---

## ✨ 功能特点

- 🧠 **多智能体协作**：Parser, Translator, Summarizer, Terminology Extractor, Generator    
- 📄 **LaTeX结构保留**：完整保留`\section`、`\label`、`\ref`、数学环境和格式  
- 🌐 **灵活后端支持**：支持GPT-4、DeepSeek或自定义LLM API  
- 📚 **ArXiv ID支持**：通过单条命令自动下载并翻译arXiv论文  
- 🧰 **可定制流程**：自由调整摘要生成、术语注入和翻译代理  
- 🌏 **多语言翻译**：当前支持🇨🇳中文和🇯🇵日文；🇰🇷韩文即将推出！

---

## 🛠️ 安装指南

### 方式一：本地安装

#### 1. 克隆仓库

```bash
git clone https://github.com/PolarisZZM/LaTeXTrans.git
cd LaTeXTrans
pip install -r requirements.txt
```

#### 2. 安装TeXLive

如需编译LaTeX文件（例如生成PDF输出），需要安装 [TeXLive](https://www.tug.org/texlive/).


### 方式二：Docker部署（推荐）

使用Docker可以避免复杂的环境配置，我们提供了两个版本的Docker镜像：

#### 🐳 Docker版本说明

| 版本 | 镜像大小 | 适用场景 |
|------|----------|----------|
| **基础版 (basic)** | ~800MB | 适合大多数标准LaTeX文档，包含中文支持 |
| **完整版 (full)** | ~5GB | 适合复杂文档，包含所有TeXLive宏包 |



#### 拉取预构建镜像

```bash
# 拉取基础版
docker pull ymdxe/latextrans:basic-latest

# 拉取完整版
docker pull ymdxe/latextrans:latest
```

#### 运行Docker容器

**Windows PowerShell示例：**

```powershell
# 翻译arXiv论文（使用论文ID）
docker run `
  -e LLM_API_KEY="your-api-key" `
  -e LLM_BASE_URL="your-base-url" `
  -e LLM_MODEL="deepseek-v3" `
  -v "${PWD}\outputs:/app/outputs" `
  ymdxe/latextrans:latest 2505.15838

# 使用本地TeX源文件
docker run `
  -e LLM_API_KEY="your-api-key" `
  -e LLM_BASE_URL="your-base-url" `
  -e LLM_MODEL="deepseek-v3" `
  -v "${PWD}\outputs:/app/outputs" `
  -v "${PWD}\tex source:/app/tex source" `
  ymdxe/latextrans:latest --source_dir "/app/tex source/2505.15838"
```

**Linux/Mac Bash示例：**

```bash
# 翻译arXiv论文（使用论文ID）
docker run \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="your-base-url" \
  -e LLM_MODEL="deepseek-v3" \
  -v "${PWD}/outputs:/app/outputs" \
  ymdxe/latextrans:latest 2505.15838

# 使用本地TeX源文件
docker run \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="your-base-url" \
  -e LLM_MODEL="deepseek-v3" \
  -v "${PWD}/outputs:/app/outputs" \
  -v "${PWD}/tex source:/app/tex source" \
  ymdxe/latextrans:latest --source_dir "/app/tex source/2505.15838"
```

#### 使用构建脚本（Windows PowerShell）

```powershell
# 构建基础版
.\build-docker.ps1 -Version basic

# 构建完整版
.\build-docker.ps1 -Version full

```

---

## ⚙️ 配置说明

### 本地配置

使用前请编辑配置文件：

```arduino
config/default.toml
```

设置语言模型的API密钥和基础URL：

```toml
[llm]
api_key = " " #your_api_key_here
base_url = " " #base url of the API
model = "deepseek-v3" #模型名称（可选）
```

### Docker环境变量配置

使用Docker时，可以通过环境变量覆盖配置文件中的设置：

- `LLM_API_KEY`: API密钥
- `LLM_BASE_URL`: API基础URL
- `LLM_MODEL`: 模型名称（如deepseek-v3）

支持OpenAI、DeepSeek、Claude或自托管LLM等服务。

---

## 🚀 使用方式

### 🔹 通过ArXiv ID翻译（推荐）

只需提供arXiv论文ID即可完成翻译：

```bash
python main.py <paper_id> (i.e. 2501.12948)
```

该命令将：

1. 从arXiv下载LaTeX源码
2. 解压到tex源文件目录
3. 运行多智能体翻译流程
4. 在outputs文件夹保存翻译后的.tex文件和编译的PDF

### 🔹 使用Docker运行

**Windows PowerShell示例：**

```powershell
# 基础版Docker
docker pull ymdxe/latextrans:basic-latest

docker run `
  -e LLM_API_KEY="your-api-key" `
  -e LLM_BASE_URL="your-base-url" `
  -e LLM_MODEL="deepseek-v3" `
  -v "${PWD}\outputs:/app/outputs" `
  ymdxe/latextrans:basic-latest 2501.12948

# 完整版Docker（适合复杂文档）
docker pull ymdxe/latextrans:latest

docker run `
  -e LLM_API_KEY="your-api-key" `
  -e LLM_BASE_URL="your-base-url" `
  -e LLM_MODEL="deepseek-v3" `
  -v "${PWD}\outputs:/app/outputs" `
  ymdxe/latextrans:latest 2501.12948
```

**Linux/Mac Bash示例：**

```bash

# 基础版Docker
docker pull ymdxe/latextrans:basic-latest

docker run \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="your-base-url" \
  -e LLM_MODEL="deepseek-v3" \
  -v "${PWD}/outputs:/app/outputs" \
  ymdxe/latextrans:basic-latest 2501.12948

# 完整版Docker（适合复杂文档）
docker pull ymdxe/latextrans:latest

docker run \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="your-base-url" \
  -e LLM_MODEL="deepseek-v3" \
  -v "${PWD}/outputs:/app/outputs" \
  ymdxe/latextrans:latest 2501.12948
```

---

## 💬 演示视频

系统演示视频： https://www.youtube.com/watch?v=tSVm_EOL7i8

## 🖼️ 翻译案例

以下是**LaTeXTrans**生成的三个真实翻译案例，左侧为原文，右侧为翻译结果。

### 📄 案例1：

<table>
  <tr>
    <td align="center"><b>原文</b></td>
    <td align="center"><b>译文</b></td>
  </tr>
  <tr>
    <td><img src="examples/case1src.png" width="100%"></td>
    <td><img src="examples/case1ch.png" width="100%"></td>
  </tr>
</table>

### 📄  案例2：

<table>
  <tr>
    <td align="center"><b>原文</b></td>
    <td align="center"><b>译文</b></td>
  </tr>
  <tr>
    <td><img src="examples/case2src.png" width="100%"></td>
    <td><img src="examples/case2ch.png" width="100%"></td>
  </tr>
</table>

### 📄 案例3：

<table>
  <tr>
    <td align="center"><b>原文</b></td>
    <td align="center"><b>译文</b></td>
  </tr>
  <tr>
    <td><img src="examples/case3src.png" width="100%"></td>
    <td><img src="examples/case3ch.png" width="100%"></td>
  </tr>
</table>

📂 **更多案例请查看[`examples/`](examples/) 文件夹**, 包含每个案例的完整翻译PDF。

---

## 🐳 Docker部署优势

1. **无需本地安装TeXLive** - Docker镜像已包含所有必要的LaTeX环境
2. **环境隔离** - 不会影响本地系统环境
3. **版本一致性** - 确保所有用户使用相同的运行环境
4. **快速部署** - 一条命令即可运行

## 📋 Docker版本选择建议

- **基础版 (basic)** - 推荐首选
  - 体积小，构建快
  - 包含中文支持和常用宏包
  - 适合90%的LaTeX文档

- **完整版 (full)** - 特殊需求
  - 包含所有TeXLive宏包
  - 适合非常复杂的文档
  - 构建时间长，镜像体积大

更多Docker使用详情请参考 [docker-versions.md](docker-versions.md)
