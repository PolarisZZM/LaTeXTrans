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

### 1. 克隆仓库

```bash
git clone https://github.com/PolarisZZM/LaTeXTrans.git
cd LaTeXTrans
pip install -r requirements.txt
```

### 2. 安装TeXLive

如需编译LaTeX文件（例如生成PDF输出），需要安装 [TeXLive](https://www.tug.org/texlive/).

## ⚙️ 配置说明

使用前请编辑配置文件：

```arduino
config/default.toml
```


设置语言模型的API密钥和基础URL：

```toml
[llm]
api_key = " " #your_api_key_here
base_url = " " #base url of the API
```

支持OpenAI、DeepSeek、Claude或自托管LLM等服务。

## 🚀 使用方式

### 🔹 通过ArXiv ID翻译（推荐）

只需提供arXiv论文ID即可完成翻译：

```bash
python main.py <paper_id> (i.e. 2501.12948)
```

该命令将：

1.从arXiv下载LaTeX源码

2.解压到tex源文件目录

3.运行多智能体翻译流程

4.在outputs文件夹保存翻译后的.tex文件和编译的PDF

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
