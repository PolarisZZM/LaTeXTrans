from typing import List, Dict, Any
import re
import os
import subprocess
import shutil
from functools import partial
# 假设你的 utils.py 文件在同一目录下
from .utils import find_main_tex_file, detect_tex_distributions, select_tex_distribution

class LaTexCompiler:
    # 修改构造函数以接收预选的 latexmk_path 和编译设置
    def __init__(self, output_latex_dir: str, latexmk_path: str, compilation_settings: dict = None, gui_status_callback=None):
        self.output_latex_dir = output_latex_dir
        # initial_latexmk_path 是在 main.py 中选择的默认路径，不会改变
        self.initial_latexmk_path = latexmk_path
        # latexmk_path 是当前编译任务使用的路径，可能会在重试时改变
        self.latexmk_path = latexmk_path
        
        # 编译设置
        self.compilation_settings = compilation_settings or {}
        self.enable_flawed = self.compilation_settings.get('enable_flawed', True)
        self.enable_switch = self.compilation_settings.get('enable_switch', True)
        self.compilation_mode = self.compilation_settings.get('mode', 'Auto (Recommended)')
        
        # GUI状态回调函数
        self.gui_status_callback = gui_status_callback

    def _auto_switch_distribution(self, remaining_distributions: Dict[str, str]) -> str:
        """Automatically switches to another distribution based on GUI settings."""
        if not self.enable_switch:
            print("❌ Distribution switching is disabled.")
            if self.gui_status_callback:
                self.gui_status_callback("❌ Distribution switching is disabled.")
            return None

        if not remaining_distributions:
            print("❌ No other LaTeX distributions available.")
            if self.gui_status_callback:
                self.gui_status_callback("❌ No other LaTeX distributions available.")
            return None

        # 自动选择第一个可用的发行版
        dist_name = list(remaining_distributions.keys())[0]
        new_path = remaining_distributions[dist_name]
        
        print(f"🔄 Automatically switching to {dist_name}: {new_path}")
        if self.gui_status_callback:
            self.gui_status_callback(f"🔄 Automatically switching to {dist_name}...")
        
        return new_path

    def compile(self):
        """
        Compile the LaTeX document using the pre-selected distribution.
        Follows the exact logic described in compile.md:
        1. Only consider compilation successful if log has no errors
        2. If pdflatex has errors, try xelatex
        3. If xelatex also has errors, ask to switch distribution
        4. If switching, start over with pdflatex
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

            main_tex_base = os.path.splitext(os.path.basename(tex_file_to_compile))[0]
            flawed_results = {}

            # 根据编译模式选择引擎
            if self.compilation_mode == "pdflatex only":
                # 只尝试pdflatex
                print(f"\nAttempting compilation with pdflatex using '{selected_dist_name}'...⏳")
                return_code_pdflatex = self._compile_with_pdflatex(tex_file_to_compile, compile_out_dir_pdflatex, engine="pdflatex")
                
                source_pdf_path_pdflatex = os.path.join(compile_out_dir_pdflatex, f"{main_tex_base}.pdf")
                log_path_pdflatex = os.path.join(compile_out_dir_pdflatex, f"{main_tex_base}.log")
                
                # 检查编译结果
                error_count = self._count_log_errors(log_path_pdflatex)
                
                # 检查是否有PDF文件生成
                if os.path.exists(source_pdf_path_pdflatex):
                    if return_code_pdflatex == 0 and error_count == 0:
                        # 完美成功：无错误
                        dest_dir = os.path.dirname(self.output_latex_dir)
                        dest_pdf_path = os.path.join(dest_dir, f"{os.path.basename(dest_dir)}.pdf")
                        print(f"✅ Successfully generated PDF with pdflatex (no errors)!")
                        if self.gui_status_callback:
                            self.gui_status_callback("✅ Perfect PDF generated with pdflatex!")
                        shutil.copy(source_pdf_path_pdflatex, dest_pdf_path)
                        return dest_pdf_path
                    else:
                        # 有错误，生成有损PDF
                        print(f"⚠️ pdflatex compilation has {error_count} errors but generated PDF.")
                        if self.gui_status_callback:
                            self.gui_status_callback(f"⚠️ PDF generated with {error_count} errors, continuing to try xelatex...")
                        if self.enable_flawed:
                            flawed_results['pdflatex'] = {'pdf_path': source_pdf_path_pdflatex, 'log_path': log_path_pdflatex}
                else:
                    # 没有生成PDF文件，编译完全失败
                    print(f"❌ pdflatex compilation failed - no PDF generated. Error count: {error_count}")
                    if self.gui_status_callback:
                        self.gui_status_callback(f"❌ pdflatex compilation failed - no PDF generated")
                    
            elif self.compilation_mode == "xelatex only":
                # 只尝试xelatex
                print(f"\nAttempting compilation with xelatex using '{selected_dist_name}'...⏳")
                return_code_xelatex = self._compile_with_xelatex(tex_file_to_compile, compile_out_dir_xelatex, engine="xelatex")
                
                source_pdf_path_xelatex = os.path.join(compile_out_dir_xelatex, f"{main_tex_base}.pdf")
                log_path_xelatex = os.path.join(compile_out_dir_xelatex, f"{main_tex_base}.log")
                
                # 检查编译结果
                error_count = self._count_log_errors(log_path_xelatex)
                
                # 检查是否有PDF文件生成
                if os.path.exists(source_pdf_path_xelatex):
                    if return_code_xelatex == 0 and error_count == 0:
                        # 完美成功：无错误
                        dest_dir = os.path.dirname(self.output_latex_dir)
                        dest_pdf_path = os.path.join(dest_dir, f"{os.path.basename(dest_dir)}.pdf")
                        print(f"✅ Successfully generated PDF with xelatex (no errors)!")
                        if self.gui_status_callback:
                            self.gui_status_callback("✅ Perfect PDF generated with xelatex!")
                        shutil.copy(source_pdf_path_xelatex, dest_pdf_path)
                        return dest_pdf_path
                    else:
                        # 有错误，生成有损PDF
                        print(f"⚠️ xelatex compilation has {error_count} errors but generated PDF.")
                        if self.gui_status_callback:
                            self.gui_status_callback(f"⚠️ PDF generated with {error_count} errors, but this is the only engine available.")
                        if self.enable_flawed:
                            flawed_results['xelatex'] = {'pdf_path': source_pdf_path_xelatex, 'log_path': log_path_xelatex}
                else:
                    # 没有生成PDF文件，编译完全失败
                    print(f"❌ xelatex compilation failed - no PDF generated. Error count: {error_count}")
                    if self.gui_status_callback:
                        self.gui_status_callback(f"❌ xelatex compilation failed - no PDF generated")
                    
            else:
                # Auto模式或Manual模式：先尝试pdflatex，再尝试xelatex
                # Attempt 1: pdflatex
                print(f"\nAttempting compilation with pdflatex using '{selected_dist_name}'...⏳")
                return_code_pdflatex = self._compile_with_pdflatex(tex_file_to_compile, compile_out_dir_pdflatex, engine="pdflatex")
                
                source_pdf_path_pdflatex = os.path.join(compile_out_dir_pdflatex, f"{main_tex_base}.pdf")
                log_path_pdflatex = os.path.join(compile_out_dir_pdflatex, f"{main_tex_base}.log")
                
                # 检查pdflatex编译结果
                error_count = self._count_log_errors(log_path_pdflatex)
                
                # 检查是否有PDF文件生成
                if os.path.exists(source_pdf_path_pdflatex):
                    if return_code_pdflatex == 0 and error_count == 0:
                        # 完美成功：无错误
                        dest_dir = os.path.dirname(self.output_latex_dir)
                        dest_pdf_path = os.path.join(dest_dir, f"{os.path.basename(dest_dir)}.pdf")
                        print(f"✅ Successfully generated PDF with pdflatex (no errors)!")
                        if self.gui_status_callback:
                            self.gui_status_callback("✅ Perfect PDF generated with pdflatex!")
                        shutil.copy(source_pdf_path_pdflatex, dest_pdf_path)
                        return dest_pdf_path
                    else:
                        # 有错误，记录为有损结果
                        print(f"⚠️ pdflatex compilation has {error_count} errors but generated PDF.")
                        if self.gui_status_callback:
                            self.gui_status_callback(f"⚠️ PDF generated with {error_count} errors, continuing to try xelatex...")
                        if self.enable_flawed:
                            flawed_results['pdflatex'] = {'pdf_path': source_pdf_path_pdflatex, 'log_path': log_path_pdflatex}
                else:
                    # 没有生成PDF文件，编译完全失败
                    print(f"❌ pdflatex compilation failed - no PDF generated. Error count: {error_count}")
                    if self.gui_status_callback:
                        self.gui_status_callback(f"❌ pdflatex compilation failed - no PDF generated")

                # Attempt 2: xelatex (当pdflatex未完美成功时尝试)
                if 'pdflatex' in flawed_results or not os.path.exists(source_pdf_path_pdflatex) or return_code_pdflatex != 0:
                    print(f"⚠️ pdflatex was not perfectly successful. Retrying with xelatex using '{selected_dist_name}'...⏳")
                    return_code_xelatex = self._compile_with_xelatex(tex_file_to_compile, compile_out_dir_xelatex, engine="xelatex")
                    
                    source_pdf_path_xelatex = os.path.join(compile_out_dir_xelatex, f"{main_tex_base}.pdf")
                    log_path_xelatex = os.path.join(compile_out_dir_xelatex, f"{main_tex_base}.log")
                    
                    # 检查xelatex编译结果
                    error_count = self._count_log_errors(log_path_xelatex)
                    
                    # 检查是否有PDF文件生成
                    if os.path.exists(source_pdf_path_xelatex):
                        if return_code_xelatex == 0 and error_count == 0:
                            # 完美成功：无错误
                            dest_dir = os.path.dirname(self.output_latex_dir)
                            dest_pdf_path = os.path.join(dest_dir, f"{os.path.basename(dest_dir)}.pdf")
                            print(f"✅ Successfully generated PDF with xelatex (no errors)!")
                            if self.gui_status_callback:
                                self.gui_status_callback("✅ Perfect PDF generated with xelatex!")
                            shutil.copy(source_pdf_path_xelatex, dest_pdf_path)
                            return dest_pdf_path
                        else:
                            # 有错误，记录为有损结果
                            print(f"⚠️ xelatex compilation has {error_count} errors but generated PDF.")
                            if self.gui_status_callback:
                                self.gui_status_callback(f"⚠️ PDF generated with {error_count} errors, considering flawed PDF options...")
                            if self.enable_flawed:
                                flawed_results['xelatex'] = {'pdf_path': source_pdf_path_xelatex, 'log_path': log_path_xelatex}
                    else:
                        # 没有生成PDF文件，编译完全失败
                        print(f"❌ xelatex compilation failed - no PDF generated. Error count: {error_count}")
                        if self.gui_status_callback:
                            self.gui_status_callback(f"❌ xelatex compilation failed - no PDF generated")

            # --- Decision Logic for Flawed PDFs ---
            if not self.enable_flawed:
                print("❌ Flawed PDF generation is disabled. Compilation failed.")
                if self.gui_status_callback:
                    self.gui_status_callback("❌ Compilation failed - flawed PDF generation is disabled.")
                return None
                
            best_flawed_result = None
            if len(flawed_results) == 1:
                winner_engine = list(flawed_results.keys())[0]
                best_flawed_result = flawed_results[winner_engine]
                print(f"ℹ️ Only {winner_engine} produced a flawed PDF. Selecting it as the best available option.")
                if self.gui_status_callback:
                    self.gui_status_callback(f"ℹ️ Only {winner_engine} produced a flawed PDF. Selecting it as the best available option.")
            elif len(flawed_results) == 2:
                print("ℹ️ Both pdflatex and xelatex produced flawed PDFs. Comparing logs to find the better one...")
                if self.gui_status_callback:
                    self.gui_status_callback("ℹ️ Both engines produced flawed PDFs. Comparing to find the better one...")
                errors_pdflatex = self._count_log_errors(flawed_results['pdflatex']['log_path'])
                errors_xelatex = self._count_log_errors(flawed_results['xelatex']['log_path'])
                print(f"   - pdflatex errors: {errors_pdflatex if errors_pdflatex != float('inf') else 'Not Found'}")
                print(f"   - xelatex errors: {errors_xelatex if errors_xelatex != float('inf') else 'Not Found'}")

                if errors_pdflatex <= errors_xelatex:
                    best_flawed_result = flawed_results['pdflatex']
                    print("   - Selecting pdflatex result as it has fewer or equal errors.")
                    if self.gui_status_callback:
                        self.gui_status_callback("   - Selecting pdflatex result as it has fewer or equal errors.")
                else:
                    best_flawed_result = flawed_results['xelatex']
                    print("   - Selecting xelatex result as it has fewer errors.")
                    if self.gui_status_callback:
                        self.gui_status_callback("   - Selecting xelatex result as it has fewer errors.")

            if best_flawed_result:
                dest_dir = os.path.dirname(self.output_latex_dir)
                dest_pdf_path = os.path.join(dest_dir, f"{os.path.basename(dest_dir)}_flawed.pdf")
                print(f"✅ Saving the best available flawed PDF to {dest_pdf_path}")
                if self.gui_status_callback:
                    self.gui_status_callback("😔 Unfortunately, only a flawed PDF could be generated. Saving as _flawed.pdf")
                shutil.copy(best_flawed_result['pdf_path'], dest_pdf_path)
                return dest_pdf_path
            
            # Both engines failed with the current distribution and produced no PDF
            print(f"❌ Compilation failed with both pdflatex and xelatex using '{selected_dist_name}', and no usable PDF was generated.")

            if not self.enable_switch:
                print("❌ Distribution switching is disabled. Compilation failed.")
                if self.gui_status_callback:
                    self.gui_status_callback("❌ Compilation failed - distribution switching is disabled.")
                return None
                
            if not distributions_to_try_next:
                print("No other LaTeX distributions to try.")
                if self.gui_status_callback:
                    self.gui_status_callback("❌ No other LaTeX distributions available. Compilation failed.")
                self.latexmk_path = None
            else:
                if self.gui_status_callback:
                    self.gui_status_callback("🔄 Switching to another LaTeX distribution...")
                self.latexmk_path = self._auto_switch_distribution(distributions_to_try_next)

        print("\nCompilation failed. Please check the logs for more details.")
        if self.gui_status_callback:
            self.gui_status_callback("❌ Compilation failed. Please check the logs for more details.")
        return None

    def _count_log_errors(self, log_file_path: str) -> int:
        """Parses a .log file to count the number of LaTeX errors."""
        if not os.path.exists(log_file_path):
            # Return a very high number if the log file doesn't even exist,
            # indicating a catastrophic failure before logging could even properly start.
            return float('inf')
        
        error_count = 0
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for compilation failure indicators
            if "Latexmk: Errors, so I did not complete making targets" in content:
                error_count += 100  # Major failure indicator
            if "command failed with exit code" in content:
                error_count += 50   # Command failure
            if "That makes" in content and "errors; please try again" in content:
                # Extract the number of errors from "That makes X errors; please try again"
                import re
                match = re.search(r"That makes (\d+) errors; please try again", content)
                if match:
                    error_count += int(match.group(1))
            
            # A comprehensive way to count LaTeX errors
            # Most critical errors that halt compilation are prefixed with "!"
            error_count += content.count("! LaTeX Error:")
            # Add other common error patterns
            error_count += content.count("! Undefined control sequence")
            error_count += content.count("! Missing $ inserted")
            error_count += content.count("! Missing } inserted")
            error_count += content.count("! Missing { inserted")
            error_count += content.count("! Missing \endcsname inserted")
            error_count += content.count("! Missing \end inserted")
            error_count += content.count("! Missing \begin inserted")
            error_count += content.count("! Missing \right inserted")
            error_count += content.count("! Missing \left inserted")
            error_count += content.count("! Missing delimiter")
            error_count += content.count("! Missing number")
            error_count += content.count("! Missing character")
            error_count += content.count("! Missing argument")
            error_count += content.count("! Missing \endcsname")
            error_count += content.count("! Missing \end")
            error_count += content.count("! Missing \begin")
            error_count += content.count("! Missing \right")
            error_count += content.count("! Missing \left")
            error_count += content.count("! Missing delimiter")
            error_count += content.count("! Missing number")
            error_count += content.count("! Missing character")
            error_count += content.count("! Missing argument")
            error_count += content.count("! Package inputenc Error")
            error_count += content.count("! Package fontspec Error")
            error_count += content.count("! Package ctex Error")
            error_count += content.count("! Package CJKutf8 Error")
            
            # Additional error patterns
            error_count += content.count("! Misplaced alignment tab character")
            error_count += content.count("! Missing $ inserted")
            error_count += content.count("! Missing } inserted")
            error_count += content.count("! Missing { inserted")
            error_count += content.count("! Missing \endcsname inserted")
            error_count += content.count("! Missing \end inserted")
            error_count += content.count("! Missing \begin inserted")
            error_count += content.count("! Missing \right inserted")
            error_count += content.count("! Missing \left inserted")
            error_count += content.count("! Missing delimiter")
            error_count += content.count("! Missing number")
            error_count += content.count("! Missing character")
            error_count += content.count("! Missing argument")
            
        except Exception as e:
            print(f"⚠️  Could not read or parse log file {log_file_path}: {e}")
            return float('inf') # Treat as worst-case scenario

        return error_count

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

        result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env, creationflags=subprocess.CREATE_NO_WINDOW)

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
            result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
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