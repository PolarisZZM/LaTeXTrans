<div align="center">

English | [中文](README_CH.md) | [日本語](README_JP.md)

</div>

# 🚀 LaTeXTrans

> **Structured LaTeX Document Translation System Based on Multi-Agent Collaboration**

---

## ✨ Key Features

- 🧠 **Multi-Agent Collaboration**: Parser, Translator, Summarizer, Terminology Extractor, Generator    
- 📄 **LaTeX Structure Preservation**: Complete preservation of `\section`, `\label`, `\ref`, mathematical environments and formatting  
- 🌐 **Flexible Backend Support**: Supports GPT-4, DeepSeek, or custom LLM APIs  
- 📚 **ArXiv ID Support**: Automatically download and translate arXiv papers with a single command  
- 🧰 **Customizable Workflow**: Freely adjust summary generation, terminology injection, and translation agents  
- 🌏 **Multi-language Translation**: Currently supports 🇨🇳 Chinese and 🇯🇵 Japanese; 🇰🇷 Korean coming soon!

---

## 🛠️ Installation Guide

### Method 1: Local Installation

#### 1. Clone Repository

```bash
git clone https://github.com/PolarisZZM/LaTeXTrans.git
cd LaTeXTrans
pip install -r requirements.txt
```

#### 2. Install TeXLive

If you need to compile LaTeX files (e.g., generate PDF output), install [TeXLive](https://www.tug.org/texlive/).

### Method 2: Docker Deployment (Recommended)

Using Docker avoids complex environment configuration. We provide two versions of Docker images:

#### 🐳 Docker Version Description

| Version | Image Size | Use Case |
|---------|------------|----------|
| **Basic (basic)** | ~800MB | Suitable for most standard LaTeX documents, includes Chinese support |
| **Full (full)** | ~5GB | Suitable for complex documents, includes all TeXLive packages |

#### Build Docker Images

```bash
# Build basic version (recommended)
docker build -f Dockerfile.basic -t ymdxe/latextrans:v1.0.0-basic .

# Build full version (if complete TeXLive support is needed)
docker build -t ymdxe/latextrans:v1.0.0 .
```

#### Run Docker Container

**Windows PowerShell Example:**

```powershell
# Translate arXiv paper (using paper ID)
docker run `
  -e LLM_API_KEY="your-api-key" `
  -e LLM_BASE_URL="your-base-url" `
  -e LLM_MODEL="deepseek-v3" `
  -v "${PWD}\outputs:/app/outputs" `
  ymdxe/latextrans:v1.0.0 2505.15838

# Use local TeX source files
docker run `
  -e LLM_API_KEY="your-api-key" `
  -e LLM_BASE_URL="your-base-url" `
  -e LLM_MODEL="deepseek-v3" `
  -v "${PWD}\outputs:/app/outputs" `
  -v "${PWD}\tex source:/app/tex source" `
  ymdxe/latextrans:v1.0.0 --source_dir "/app/tex source/2505.15838"
```

**Linux/Mac Bash Example:**

```bash
# Translate arXiv paper (using paper ID)
docker run \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="your-base-url" \
  -e LLM_MODEL="deepseek-v3" \
  -v "${PWD}/outputs:/app/outputs" \
  ymdxe/latextrans:v1.0.0 2505.15838

# Use local TeX source files
docker run \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="your-base-url" \
  -e LLM_MODEL="deepseek-v3" \
  -v "${PWD}/outputs:/app/outputs" \
  -v "${PWD}/tex source:/app/tex source" \
  ymdxe/latextrans:v1.0.0 --source_dir "/app/tex source/2505.15838"
```

#### Using Build Script (Windows PowerShell)

```powershell
# Build basic version
.\build-docker.ps1 -Version basic

# Build full version
.\build-docker.ps1 -Version full

# Build all versions
.\build-docker.ps1 -Version all
```

### Method 3：Install via pip (Recommended)

We provide a pre-packaged pip installation for easy setup, eliminating the need for complex code management.

```pip
pip intsall latextrans

# Launch with GUI 
latextrans -g
```

For detailed usage parameters, please refer to the CLI execution options described later.
---

## ⚙️ Configuration Guide

### Local Configuration

Please edit the configuration file before use:

```arduino
config/default.toml
```

Set the language model's API key and base URL:

```toml
[llm]
api_key = " " #your_api_key_here
base_url = " " #base url of the API
model = "deepseek-v3" #model name (optional)
```

### Docker Environment Variable Configuration

When using Docker, you can override configuration file settings with environment variables:

- `LLM_API_KEY`: API key
- `LLM_BASE_URL`: API base URL
- `LLM_MODEL`: Model name (e.g., deepseek-v3)

Supports services like OpenAI, DeepSeek, Claude, or self-hosted LLMs.

---

## 🚀 Usage

### 🔹 Translation via ArXiv ID (Recommended)

Simply provide an arXiv paper ID to complete translation:

```bash
python main.py <paper_id> (i.e. 2501.12948)
```

This command will:

1. Download LaTeX source code from arXiv
2. Extract to tex source file directory
3. Run multi-agent translation workflow
4. Save translated .tex files and compiled PDF in outputs folder

### 🔹 Running with Docker

**Windows PowerShell Example:**

```powershell
# Basic Docker version
docker run `
  -e LLM_API_KEY="your-api-key" `
  -e LLM_BASE_URL="your-base-url" `
  -e LLM_MODEL="deepseek-v3" `
  -v "${PWD}\outputs:/app/outputs" `
  ymdxe/latextrans:v1.0.0-basic 2501.12948

# Full Docker version (suitable for complex documents)
docker run `
  -e LLM_API_KEY="your-api-key" `
  -e LLM_BASE_URL="your-base-url" `
  -e LLM_MODEL="deepseek-v3" `
  -v "${PWD}\outputs:/app/outputs" `
  ymdxe/latextrans:v1.0.0 2501.12948
```

**Linux/Mac Bash Example:**

```bash
# Basic Docker version
docker run \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="your-base-url" \
  -e LLM_MODEL="deepseek-v3" \
  -v "${PWD}/outputs:/app/outputs" \
  ymdxe/latextrans:v1.0.0-basic 2501.12948

# Full Docker version (suitable for complex documents)
docker run \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="your-base-url" \
  -e LLM_MODEL="deepseek-v3" \
  -v "${PWD}/outputs:/app/outputs" \
  ymdxe/latextrans:v1.0.0 2501.12948
```


### 🔹 Running with CLI

| Option                | Function                                                                                                      | Example                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `--config`            | Path to the config TOML file                        | `python main.py --config Path/config.toml`                                    |
| `--model`             | LLM for translating.                                | `python main.py --model deepseek-v3`                      |
| `--url`               | Model url                                           | `python main.py --url your url`                    |
| `--key`               | Model API key                                       | `python main.py --key your APIkey`                    |
| `--Arxiv`             | Arxiv paper ID                                      | `python main.py --Arxiv 2307.07924`                  |
| `--GUI`or`-g`         | Interact with GUI                                   | `python main.py -g`                      |
| `--mode`              | Translate mode                                      | `python main.py --mode 2`                      |
| `--update_term`       | Update term or not                                  | `python main.py --update_term Ture`                      |
| `--tl`                | Target language                                     | `python main.py --tl ch`                      |
| `--sl`                | Source language                                     | `python main.py --sl en`                      |
| `--ut`                | User's term dict                                    | `python main.py --ut Path/Yourterm.csv`                      |
| `--output`            | output directory                                    | `python main.py --output Path`                      |
| `--source`            | tex source directory                                | `python main.py --sourse Path`                      |
| `--save_config`       | Path to save config                                 | `python main.py --save_config savePath`                      |

*The system accepts arXiv paper IDs in either canonical ID format or as clickable arXiv paper URLs.

*For initial setup, users may launch the system by directly modifying the config/default.toml file.

*We recommend novice users utilize the graphical interface for a more streamlined experience.
---

## 💬 Demo Video

System demonstration video: https://www.youtube.com/watch?v=tSVm_EOL7i8

## 🖼️ Translation Examples

The following are three real translation examples generated by **LaTeXTrans**, with the original text on the left and translation results on the right.

### 📄 Case 1:

<table>
  <tr>
    <td align="center"><b>Original</b></td>
    <td align="center"><b>Translation</b></td>
  </tr>
  <tr>
    <td><img src="examples/case1src.png" width="100%"></td>
    <td><img src="examples/case1ch.png" width="100%"></td>
  </tr>
</table>

### 📄 Case 2:

<table>
  <tr>
    <td align="center"><b>Original</b></td>
    <td align="center"><b>Translation</b></td>
  </tr>
  <tr>
    <td><img src="examples/case2src.png" width="100%"></td>
    <td><img src="examples/case2ch.png" width="100%"></td>
  </tr>
</table>

### 📄 Case 3:

<table>
  <tr>
    <td align="center"><b>Original</b></td>
    <td align="center"><b>Translation</b></td>
  </tr>
  <tr>
    <td><img src="examples/case3src.png" width="100%"></td>
    <td><img src="examples/case3ch.png" width="100%"></td>
  </tr>
</table>

📂 **See [`examples/`](examples/) folder for more cases**, including complete translation PDFs for each case.

---

## 🐳 Docker Deployment Advantages

1. **No local TeXLive installation required** - Docker image includes all necessary LaTeX environments
2. **Environment isolation** - Does not affect local system environment
3. **Version consistency** - Ensures all users use the same runtime environment
4. **Quick deployment** - Run with a single command

## 📋 Docker Version Selection Recommendations

- **Basic (basic)** - First choice recommendation
  - Small size, fast build
  - Includes Chinese support and common packages
  - Suitable for 90% of LaTeX documents

- **Full (full)** - Special requirements
  - Includes all TeXLive packages
  - Suitable for very complex documents
  - Long build time, large image size

For more Docker usage details, please refer to [docker-versions.md](docker-versions.md)
