# LaTeXTrans Docker 版本说明

## 版本对比

| 版本 | Dockerfile | 镜像大小（预估） | 包含的LaTeX包 | 适用场景 |
|------|------------|-----------------|---------------|----------|
| **基础版 (basic)** | Dockerfile.basic | ~800MB | texlive, texlive-latex-base, texlive-latex-recommended, texlive-fonts-recommended, texlive-lang-chinese, texlive-xetex | 适合大多数标准LaTeX文档，支持中文 |
| **轻量版 (light)** | Dockerfile.light | ~1.5GB | texlive-latex-base, texlive-latex-recommended, texlive-fonts-recommended, texlive-latex-extra, texlive-xetex | 适合需要额外宏包但不需要完整TeXLive的场景 |
| **完整版 (full)** | Dockerfile | ~5GB | texlive-full | 适合复杂文档，包含所有TeXLive宏包 |

## 构建说明

### 1. 修复Docker镜像源问题

在构建之前，请确保已经解决了Docker镜像源的问题。参考 `docker-fix-guide.md`。

### 2. 使用构建脚本

```powershell
# 构建基础版（推荐）
.\build-docker.ps1 -Version basic

# 构建轻量版
.\build-docker.ps1 -Version light

# 构建完整版
.\build-docker.ps1 -Version full

# 构建所有版本
.\build-docker.ps1 -Version all

# 指定自定义标签
.\build-docker.ps1 -Version basic -Tag v2.0.0
```

### 3. 手动构建

```bash
# 构建基础版
docker build -f Dockerfile.basic -t ymdxe/latextrans:v1.0.0-basic .

# 构建轻量版
docker build -f Dockerfile.light -t ymdxe/latextrans:v1.0.0-light .

# 构建完整版
docker build -f Dockerfile -t ymdxe/latextrans:v1.0.0-full .
```

## 使用说明

### 运行容器

```bash
# 使用基础版
docker run -v ${PWD}/outputs:/app/outputs \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="your-base-url" \
  ymdxe/latextrans:v1.0.0-basic

# 使用轻量版
docker run -v ${PWD}/outputs:/app/outputs \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="your-base-url" \
  ymdxe/latextrans:v1.0.0-light

# 使用完整版
docker run -v ${PWD}/outputs:/app/outputs \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="your-base-url" \
  ymdxe/latextrans:v1.0.0-full
```

### 传递参数

```bash
# 翻译特定的arXiv论文
docker run -v ${PWD}/outputs:/app/outputs \
  -e LLM_API_KEY="your-api-key" \
  ymdxe/latextrans:v1.0.0-basic \
  --arxiv_id 2505.15838

# 使用本地TeX源文件
docker run -v ${PWD}/tex_source:/app/tex_source \
  -v ${PWD}/outputs:/app/outputs \
  -e LLM_API_KEY="your-api-key" \
  ymdxe/latextrans:v1.0.0-basic \
  --source_dir /app/tex_source/your_paper
```

## 版本选择建议

1. **基础版 (basic)** - 推荐首选
   - 体积小，构建快
   - 包含中文支持
   - 适合90%的LaTeX文档

2. **轻量版 (light)** - 中等需求
   - 包含更多常用宏包
   - 适合需要特殊宏包的文档

3. **完整版 (full)** - 特殊需求
   - 包含所有TeXLive宏包
   - 适合非常复杂的文档
   - 构建时间长，镜像体积大

## 故障排除

### 构建失败

1. 检查Docker镜像源配置
2. 确保网络连接正常
3. 尝试使用 `fix-docker-build.ps1` 脚本

### 运行时错误

1. 检查是否正确挂载了卷
2. 确保提供了必要的环境变量
3. 查看容器日志：`docker logs <container-id>`

### LaTeX编译失败

- 基础版缺少某些宏包时，尝试使用轻量版或完整版
- 检查LaTeX源文件是否有语法错误
- 查看编译日志了解具体错误信息
