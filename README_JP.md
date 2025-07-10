<div align="center">

[English](README.md) | [中文](README_CH.md) | 日本語

</div>

# 🚀 LaTeXTrans

> **マルチエージェント協調に基づく構造化LaTeX文書翻訳システム**

---

## ✨ 特徴

- 🧠 **マルチエージェント協調**：Parser, Translator, Summarizer, Terminology Extractor, Generator  
- 📄 **LaTeX構造の保持**：\section、\label、\ref、数式環境、書式を完全保持  
- 🌐 **柔軟なバックエンド対応**：GPT-4、DeepSeekまたは独自LLM APIに対応 
- 📚 **AarXiv IDサポート**：コマンド1つでarXiv論文を自動ダウンロード＆翻訳 
- 🧰 **カスタマイズ可能なパイプライン**：要約生成、専門用語注入、翻訳エージェントを自由調整 
- 🌏 **多言語翻訳**：現在🇨🇳中国語と🇯🇵日本語に対応、🇰🇷韓国語も近日公開予定！

---

## 🛠️ インストール方法

### 1. リポジトリのクローン

```bash
git clone https://github.com/PolarisZZM/LaTeXTrans.git
cd LaTeXTrans
pip install -r requirements.txt
```

### 2. TeXLiveのインストール

LaTeXファイルのコンパイル（PDF出力など）には[TeXLive](https://www.tug.org/texlive/)のインストールが必要です。
## ⚙️ 設定方法

使用前に設定ファイルを編集してください:

```arduino
config/default.toml
```


言語モデルのAPIキーとベースURLを設定:

```toml
[llm]
api_key = " " #your_api_key_here
base_url = " " #base url of the API
```

OpenAI、DeepSeek、Claudeまたは自社ホスト型LLMなどに対応しています。

## 🚀 使用方式

### 🔹 arXiv IDでの実行（推奨）

arXiv論文IDを指定するだけで翻訳可能:

```bash
python main.py <paper_id> (i.e. 2501.12948)
```

このコマンドで以下が自動実行されます:

1.arXivからLaTeXソースをダウンロード

2.texソースフォルダに展開

3.マルチエージェント翻訳パイプラインを実行

4.翻訳済み.texファイルとコンパイル済みPDFをoutputsフォルダに保存

## 💬 デモ動画

システムデモ動画: https://www.youtube.com/watch?v=tSVm_EOL7i8

## 🖼️翻訳事例

**LaTeXTrans**で生成した3つの実際の翻訳事例です。左側が原文、右側が翻訳結果です。

### 📄  案例1：

<table>
  <tr>
    <td align="center"><b>原文</b></td>
    <td align="center"><b>翻訳</b></td>
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
    <td align="center"><b>翻訳</b></td>
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
    <td align="center"><b>翻訳</b></td>
  </tr>
  <tr>
    <td><img src="examples/case3src.png" width="100%"></td>
    <td><img src="examples/case3ch.png" width="100%"></td>
  </tr>
</table>


📂 **その他の事例は[`examples/`](examples/) フォルダ**, でご覧いただけます。各事例の完全な翻訳PDFも含まれています。