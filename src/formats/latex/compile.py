from typing import List, Dict, Any
import re
import os
import subprocess
import shutil
import platform
from functools import partial
# 假设你的 utils.py 文件在同一目录下
from .utils import find_main_tex_file, detect_tex_distributions, select_tex_distribution

class LaTexCompiler:
    # 修改构造函数以接收预选的 latexmk_path
    def __init__(self, output_latex_dir: str, latexmk_path: str):
        self.output_latex_dir = output_latex_dir
        # initial_latexmk_path 是在 main.py 中选择的默认路径，不会改变
        self.initial_latexmk_path = latexmk_path
        # latexmk_path 是当前编译任务使用的路径，可能会在重试时改变
        self.latexmk_path = latexmk_path

    def _ask_and_switch_distribution(self, remaining_distributions: Dict[str, str]) -> str:
        """Asks the user to switch, lets them select a new distribution, and returns the new path."""
        print("\nDo you want to try compiling with a different LaTeX distribution?")
        while True:
            switch_choice = input("Enter 'yes' to switch, 'no' to abort: ").lower().strip()
            if switch_choice in ['yes', 'no']:
                break
            print("Invalid input. Please enter 'yes' or 'no'.")

        if switch_choice == 'no':
            return None

        # 用户想要切换，从剩余发行版中选择
        new_path = select_tex_distribution(remaining_distributions)
        return new_path

    def compile(self):
        """
        Compile the LaTeX document using the pre-selected distribution,
        with an option to switch to another on failure.
        """
        self.latexmk_path = self.initial_latexmk_path
        
        if not self.latexmk_path:
            print("❌ Error: No LaTeX distribution path was provided to the compiler.")
            return None

        all_distributions = detect_tex_distributions()
        
        while self.latexmk_path:
            selected_dist_name = next((name for name, path in all_distributions.items() if path == self.latexmk_path), "Unknown")
            
            distributions_to_try_next = all_distributions.copy()
            if selected_dist_name in distributions_to_try_next:
                del distributions_to_try_next[selected_dist_name]

            print(f"🧹 Cleaning up previous build directories before attempting with '{selected_dist_name}'...")
            compile_out_dir_pdflatex = os.path.join(self.output_latex_dir, "build_pdflatex")
            compile_out_dir_xelatex = os.path.join(self.output_latex_dir, "build_xelatex")
            if os.path.exists(compile_out_dir_pdflatex): shutil.rmtree(compile_out_dir_pdflatex)
            if os.path.exists(compile_out_dir_xelatex): shutil.rmtree(compile_out_dir_xelatex)
            tex_file_to_compile = find_main_tex_file(self.output_latex_dir)
            if not tex_file_to_compile:
                print("⚠️ Warning: There is no main tex file to compile in this directory.")
                return None

            # Attempt 1: pdflatex
            print(f"\nAttempting compilation with pdflatex using '{selected_dist_name}'...⏳")
            return_code_pdflatex = self._compile_with_pdflatex(tex_file_to_compile, compile_out_dir_pdflatex, engine="pdflatex")
            
            if return_code_pdflatex == 0:
                main_tex_base = os.path.splitext(os.path.basename(tex_file_to_compile))[0]
                source_pdf_path = os.path.join(compile_out_dir_pdflatex, f"{main_tex_base}.pdf")
                if os.path.exists(source_pdf_path):
                    dest_dir = os.path.dirname(self.output_latex_dir)
                    dest_pdf_path = os.path.join(dest_dir, f"{os.path.basename(dest_dir)}.pdf")
                    print(f"✅ Successfully generated PDF with pdflatex!")
                    shutil.copy(source_pdf_path, dest_pdf_path)
                    return dest_pdf_path

            # Attempt 2: xelatex
            print(f"⚠️ Failed to generate PDF with pdflatex. Retrying with xelatex using '{selected_dist_name}'...⏳")
            return_code_xelatex = self._compile_with_xelatex(tex_file_to_compile, compile_out_dir_xelatex, engine="xelatex")
            
            if return_code_xelatex == 0:
                main_tex_base = os.path.splitext(os.path.basename(tex_file_to_compile))[0]
                source_pdf_path = os.path.join(compile_out_dir_xelatex, f"{main_tex_base}.pdf")
                if os.path.exists(source_pdf_path):
                    dest_dir = os.path.dirname(self.output_latex_dir)
                    dest_pdf_path = os.path.join(dest_dir, f"{os.path.basename(dest_dir)}.pdf")
                    print(f"✅ Successfully generated PDF with xelatex!")
                    shutil.copy(source_pdf_path, dest_pdf_path)
                    return dest_pdf_path

            # Both engines failed with the current distribution
            print(f"❌ Compilation failed with both pdflatex and xelatex using '{selected_dist_name}'.")

            if not distributions_to_try_next:
                print("No other LaTeX distributions to try.")
                self.latexmk_path = None
            else:
                self.latexmk_path = self._ask_and_switch_distribution(distributions_to_try_next)

        print("\nCompilation failed. Please check the logs for more details.")
        return None

    def compile_ja(self):
        # 此方法保持不变
        tex_file_to_compile = find_main_tex_file(self.output_latex_dir)
        if not tex_file_to_compile:
            print("⚠️ Warning: There is no main tex file to compile in this directory.")
            return None
        print("Start compiling with lualatex...⏳")
        compile_out_dir_lualatex = os.path.join(self.output_latex_dir, "build_lualatex")
        # 假设你有一个 _compile_with_lualatex 方法
        # return_code_lualatex = self._compile_with_lualatex(tex_file_to_compile, compile_out_dir_lualatex, engine="lualatex")
        # 暂时返回None，因为缺少_compile_with_lualatex的定义
        print("Function `_compile_with_lualatex` is not defined in the provided code.")
        return None

    def _compile_with_pdflatex(self,
                               tex_file: str, 
                               out_dir: str, 
                               engine: str = "pdflatex"):
        
        source_dir = os.path.dirname(tex_file)
        main_tex_filename = os.path.basename(tex_file)

        try:
            shutil.copytree(source_dir, out_dir, ignore=shutil.ignore_patterns('build_*'))
        except Exception as e:
            print(f"❌ Error copying source files to build directory: {e}")
            return -1

        # ==================== PDFLATEX 预处理开始 ====================
        # 为编译中文文档，需要移除的其他常见语言宏包
        PACKAGES_TO_REMOVE = ['kotex', 'babel'] 

        print(f"ℹ️  正在为 `{engine}` 扫描并移除冲突的语言宏包...")
        try:
            for root, _, files in os.walk(out_dir):
                for filename in files:
                    if filename.endswith(('.tex', '.cls', '.sty')):
                        file_path = os.path.join(root, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            original_content = content
                            modified_content = content

                            # 移除指定的冲突宏包
                            for pkg_to_remove in PACKAGES_TO_REMOVE:
                                pkg_pattern = re.compile(
                                    r"^\s*\\usepackage.*\{.*?" + re.escape(pkg_to_remove) + r".*?\}.*?$",
                                    re.MULTILINE
                                )
                                modified_content = pkg_pattern.sub("", modified_content)

                            if original_content != modified_content:
                                print(f"   - 正在修正文件: {os.path.relpath(file_path, out_dir)}")
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(modified_content)

                        except Exception as e:
                            print(f"⚠️  处理文件 {file_path} 时发生错误: {e}")
        except Exception as e:
            print(f"❌ 预处理文件时发生严重错误: {e}")
            return -1
        
        # 针对主 .tex 文件，插入 CJK 环境
        tex_file_in_build_dir = os.path.join(out_dir, main_tex_filename)
        try:
            with open(tex_file_in_build_dir, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except FileNotFoundError:
            print(f"❌ Error: Main TeX file not found at {tex_file_in_build_dir}")
            return -1

        pdflatex_packages = "\\usepackage{CJKutf8}\n\\usepackage[utf8]{inputenc}"
        modified_content = original_content.replace("%%CHINESE_PACKAGE_PLACEHOLDER%%", pdflatex_packages)
        
        modified_content = re.sub(r"(\\begin\{document\})", r"\1\n\\begin{CJK*}{UTF8}{gbsn}", modified_content, count=1)
        modified_content = re.sub(r"(\\end\{document\})", r"\\end{CJK*}\n\1", modified_content, count=1)
        modified_content = modified_content.replace(r'\(s_{\max}}\)', r'\(s_{\max}\)')

        with open(tex_file_in_build_dir, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        # ==================== PDFLATEX 预处理结束 ====================

        cmd = [ self.latexmk_path, f"-{engine}", "-interaction=nonstopmode", f"-file-line-error", f"-synctex=1", main_tex_filename ]
        cwd = out_dir
        env = os.environ.copy()
        dist_bin_dir = os.path.dirname(self.latexmk_path)
        env['PATH'] = f"{dist_bin_dir}{os.pathsep}{env.get('PATH', '')}"

        # CREATE_NO_WINDOW is only available on Windows
        if platform.system() == "Windows":
            result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env)

        if result.returncode != 0:
            print(f"⚠️  `{engine}` process finished with non-zero exit code ({result.returncode}).")
            stdout = result.stdout.decode('utf-8', errors='ignore')
            if stdout.strip(): print(f"--- {engine} stdout ---\n{stdout}\n---")
            stderr = result.stderr.decode('utf-8', errors='ignore')
            if stderr.strip(): print(f"--- {engine} stderr ---\n{stderr}\n---")
            
        return result.returncode

    def _compile_with_xelatex(self,
                               tex_file: str, 
                               out_dir: str, 
                               engine: str = "xelatex"):
        
        source_dir = os.path.dirname(tex_file)
        main_tex_filename = os.path.basename(tex_file)

        if os.path.abspath(source_dir) != os.path.abspath(out_dir):
            if os.path.exists(out_dir):
                try:
                    shutil.rmtree(out_dir)
                except Exception as e:
                    print(f"❌ 删除旧的构建目录失败: {e}")
                    return -1
            try:
                shutil.copytree(source_dir, out_dir, ignore=shutil.ignore_patterns('build_*'))
            except Exception as e:
                print(f"❌ 拷贝源文件到构建目录失败: {e}")
                return -1

        # ==================== XELATEX 预处理开始 ====================
        INCOMPATIBLE_XELATEX_OPTIONS = ['pdftex', 'dvips', 'dvipdfm']
        PACKAGES_TO_REMOVE = [
            # --- 核心冲突包 ---
            'kotex',        # 韩文支持宏包
            'babel',        # 传统的、支持多种西文的宏包
            'polyglossia',  # 现代的（用于Xe/LuaLaTeX）多语言支持宏包，是 babel 的替代品

            # --- 日文支持包（非常容易与中文冲突） ---
            'luatexja',     # LuaLaTeX 下的日文宏包
            'zxjatype',     # XeLaTeX 下的日文宏包
            'platex',       # platex 引擎相关的日文宏包
            'jsclasses',    # 一套日文文档类 (article, report, book)

            # --- 其他常见语言包 ---
            'xgreek',       # XeLaTeX 下的希腊语支持
            'arabxetex',    # XeLaTeX 下的阿拉伯语支持
        ]

        def remove_incompatible_options(match, incompatible_options):
            command, options_str, package_part = match.group(1), match.group(2), match.group(3)
            options_list = [opt.strip() for opt in options_str.split(',')]
            cleaned_options = [opt for opt in options_list if opt.lower() not in incompatible_options and opt]
            new_options_str = ','.join(cleaned_options)
            if new_options_str:
                return f"{command}[{new_options_str}]{package_part}"
            else:
                return f"{command}{package_part}"

        replacer = partial(remove_incompatible_options, incompatible_options=INCOMPATIBLE_XELATEX_OPTIONS)
        package_option_pattern = re.compile(
            r"(\\documentclass|\\usepackage|\\RequirePackage)\[([^\]]*)\](\{.*?\})", 
            re.IGNORECASE
        )

        print(f"ℹ️  正在为 `{engine}` 扫描并修正不兼容的宏包、选项和命令...")
        try:
            for root, _, files in os.walk(out_dir):
                for filename in files:
                    if filename.endswith(('.tex', '.cls', '.sty')):
                        file_path = os.path.join(root, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            original_content = content
                            modified_content = content

                            # 第1步：处理方括号内的宏包选项
                            modified_content = package_option_pattern.sub(replacer, modified_content)
                            
                            # 第2步：处理独立的、不兼容的命令
                            pdfoutput_pattern = re.compile(r"^\s*\\pdfoutput\s*=\s*1\s*$", re.MULTILINE)
                            modified_content = pdfoutput_pattern.sub("", modified_content)
                            
                            # 第3步：移除指定的冲突宏包
                            for pkg_to_remove in PACKAGES_TO_REMOVE:
                                pkg_pattern = re.compile(
                                    r"^\s*\\usepackage.*\{.*?" + re.escape(pkg_to_remove) + r".*?\}.*?$",
                                    re.MULTILINE
                                )
                                modified_content = pkg_pattern.sub("", modified_content)

                            if original_content != modified_content:
                                print(f"   - 正在修正文件: {os.path.relpath(file_path, out_dir)}")
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(modified_content)

                        except Exception as e:
                            print(f"⚠️  处理文件 {file_path} 时发生错误: {e}")
        except Exception as e:
            print(f"❌ 预处理文件时发生严重错误: {e}")
            return -1

        tex_file_in_build_dir = os.path.join(out_dir, main_tex_filename)
        try:
            with open(tex_file_in_build_dir, 'r', encoding='utf-8') as f:
                main_content = f.read()
        except FileNotFoundError:
            print(f"❌ 未找到主 TeX 文件: {tex_file_in_build_dir}")
            return -1

        xelatex_package = "\\usepackage{ctex}" 
        modified_content = main_content.replace("%%CHINESE_PACKAGE_PLACEHOLDER%%", xelatex_package)
        modified_content = modified_content.replace(r'\(s_{\max}}\)', r'\(s_{\max}\)')

        try:
            with open(tex_file_in_build_dir, 'w', encoding='utf-8') as f:
                f.write(modified_content)
        except Exception as e:
            print(f"❌ 写入修改后的 TeX 文件失败: {e}")
            return -1
        # ==================== XELATEX 预处理结束 ====================

        cmd = [ self.latexmk_path, f"-{engine}", "-interaction=nonstopmode", f"-file-line-error", f"-synctex=1", main_tex_filename ]
        cwd = out_dir
        env = os.environ.copy()
        dist_bin_dir = os.path.dirname(self.latexmk_path)
        env['PATH'] = f"{dist_bin_dir}{os.pathsep}{env.get('PATH', '')}"

        try:
            print(f"🚀 开始使用 `{engine}` 进行编译...")
            # CREATE_NO_WINDOW is only available on Windows
            if platform.system() == "Windows":
                result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env)
        except Exception as e:
            print(f"❌ 编译过程中发生异常: {e}")
            return -1

        if result.returncode != 0:
            print(f"⚠️  `{engine}` 进程返回非零退出码 ({result.returncode})。")
            stdout = result.stdout.decode('utf-8', errors='ignore')
            if stdout.strip(): print(f"--- {engine} stdout ---\n{stdout}\n---")
            stderr = result.stderr.decode('utf-8', errors='ignore')
            if stderr.strip(): print(f"--- {engine} stderr ---\n{stderr}\n---")
            
        return result.returncode
