# Docker构建脚本 - 支持多个版本

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("full", "light", "basic", "all")]
    [string]$Version = "basic",
    
    [Parameter(Mandatory=$false)]
    [string]$Tag = "v1.0.0"
)

Write-Host "LaTeXTrans Docker 构建脚本" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# 设置环境变量以绕过可能的配置问题
$env:DOCKER_BUILDKIT = "0"

function Build-DockerImage {
    param(
        [string]$DockerFile,
        [string]$ImageTag,
        [string]$Description
    )
    
    Write-Host "`n构建 $Description 版本..." -ForegroundColor Yellow
    Write-Host "使用 Dockerfile: $DockerFile" -ForegroundColor Cyan
    Write-Host "镜像标签: $ImageTag" -ForegroundColor Cyan
    
    $cmd = "docker build -f $DockerFile -t $ImageTag ."
    Write-Host "执行命令: $cmd" -ForegroundColor Gray
    
    Invoke-Expression $cmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $Description 版本构建成功！" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ $Description 版本构建失败！" -ForegroundColor Red
        return $false
    }
}

# 构建指定版本
switch ($Version) {
    "full" {
        Build-DockerImage -DockerFile "Dockerfile" -ImageTag "ymdxe/latextrans:$Tag-full" -Description "完整版（texlive-full）"
    }
    "light" {
        Build-DockerImage -DockerFile "Dockerfile.light" -ImageTag "ymdxe/latextrans:$Tag-light" -Description "轻量版"
    }
    "basic" {
        Build-DockerImage -DockerFile "Dockerfile.basic" -ImageTag "ymdxe/latextrans:$Tag-basic" -Description "基础版"
    }
    "all" {
        Write-Host "`n构建所有版本..." -ForegroundColor Magenta
        $results = @()
        $results += Build-DockerImage -DockerFile "Dockerfile.basic" -ImageTag "ymdxe/latextrans:$Tag-basic" -Description "基础版"
        $results += Build-DockerImage -DockerFile "Dockerfile.light" -ImageTag "ymdxe/latextrans:$Tag-light" -Description "轻量版"
        $results += Build-DockerImage -DockerFile "Dockerfile" -ImageTag "ymdxe/latextrans:$Tag-full" -Description "完整版（texlive-full）"
        
        Write-Host "`n构建总结：" -ForegroundColor Yellow
        if ($results[0]) { Write-Host "  ✅ 基础版构建成功" -ForegroundColor Green } else { Write-Host "  ❌ 基础版构建失败" -ForegroundColor Red }
        if ($results[1]) { Write-Host "  ✅ 轻量版构建成功" -ForegroundColor Green } else { Write-Host "  ❌ 轻量版构建失败" -ForegroundColor Red }
        if ($results[2]) { Write-Host "  ✅ 完整版构建成功" -ForegroundColor Green } else { Write-Host "  ❌ 完整版构建失败" -ForegroundColor Red }
    }
}

Write-Host "`n查看已构建的镜像：" -ForegroundColor Yellow
docker images | Select-String "ymdxe/latextrans"

Write-Host "`n使用示例：" -ForegroundColor Yellow
Write-Host "  运行基础版: docker run -v `${PWD}/outputs:/app/outputs ymdxe/latextrans:$Tag-basic" -ForegroundColor Cyan
Write-Host "  运行轻量版: docker run -v `${PWD}/outputs:/app/outputs ymdxe/latextrans:$Tag-light" -ForegroundColor Cyan
Write-Host "  运行完整版: docker run -v `${PWD}/outputs:/app/outputs ymdxe/latextrans:$Tag-full" -ForegroundColor Cyan
