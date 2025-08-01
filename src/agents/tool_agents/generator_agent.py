from typing import Dict, Any, List
from src.agents.tool_agents.base_tool_agent import BaseToolAgent
from pathlib import Path
import sys
import os
import shutil

import streamlit as st
import time

base_dir = os.getcwd()
sys.path.append(base_dir)


class GeneratorAgent(BaseToolAgent):
    def __init__(self, 
                 config: Dict[str, Any],
                 project_dir: str = None,
                 output_dir: str = None,
                 latexmk_path: str = None 
                 ):
        super().__init__(agent_name="GeneratorAgent", config=config)
        self.config = config
        self.project_dir = project_dir
        self.output_dir = output_dir
        self.latexmk_path = latexmk_path
        # 从配置中获取目标语言
        self.target_language = config.get("target_language", "ch") 

    def execute(self) -> Any:
        sys.stderr = open(os.devnull, 'w')
        self.process_b = st.empty()
        with self.process_b:
            self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        sys.stderr = sys.__stderr__
        
        self.log(f"🤖💬 Start generating for project...⏳: {os.path.basename(self.project_dir)}.")

        sys.stderr = open(os.devnull, 'w')
        self.status_text.text("🔄 Start generating for project...")
        self.progress_bar.progress(5)
        sys.stderr = sys.__stderr__

        from src.formats.latex.compile import LaTexCompiler
        from src.formats.latex.reconstruct import LatexConstructor

        sys.stderr = open(os.devnull, 'w')
        self.status_text.text("📂 Reading...")
        self.progress_bar.progress(10)
        sys.stderr = sys.__stderr__
        sections = self.read_file(Path(self.output_dir, "sections_map.json"), "json")
        sys.stderr = open(os.devnull, 'w')
        self.progress_bar.progress(20)
        sys.stderr = sys.__stderr__
        captions = self.read_file(Path(self.output_dir, "captions_map.json"), "json")
        sys.stderr = open(os.devnull, 'w')
        self.progress_bar.progress(30)
        sys.stderr = sys.__stderr__
        envs = self.read_file(Path(self.output_dir, "envs_map.json"), "json")
        sys.stderr = open(os.devnull, 'w')
        self.progress_bar.progress(40)
        sys.stderr = sys.__stderr__
        newcommands = self.read_file(Path(self.output_dir, "newcommands_map.json"), "json")
        sys.stderr = open(os.devnull, 'w')
        self.progress_bar.progress(50)
        sys.stderr = sys.__stderr__
        inputs = self.read_file(Path(self.output_dir, "inputs_map.json"), "json")
        sys.stderr = open(os.devnull, 'w')
        self.progress_bar.progress(60)

        self.status_text.text("📁 Creating translation project directory ..")
        sys.stderr = sys.__stderr__

        # 创建翻译后的LaTeX目录
        base_name = os.path.basename(self.project_dir)
        transed_latex_dir = os.path.join(self.output_dir, f"{self.target_language}_{base_name}")
        transed_latex_dir = self._creat_transed_latex_folder(self.project_dir, transed_latex_dir)

        sys.stderr = open(os.devnull, 'w')
        self.progress_bar.progress(70)
        sys.stderr = sys.__stderr__

        print(transed_latex_dir)

        sys.stderr = open(os.devnull, 'w')
        self.status_text.text("🔨 Refactoring LaTeX document...")
        sys.stderr = sys.__stderr__
        latex_constructor = LatexConstructor(
                                sections=sections,
                                captions=captions,
                                envs=envs,
                                inputs=inputs,
                                newcommands=newcommands,
                                output_latex_dir=transed_latex_dir
                             )
        latex_constructor.construct()

        sys.stderr = open(os.devnull, 'w')
        self.progress_bar.progress(80)
        self.status_text.text("🛠️ Compiling PDF document...")
        sys.stderr = sys.__stderr__

        # 获取编译设置（从GUI传入）
        compilation_settings = getattr(self, 'compilation_settings', {})
        
        # 创建GUI状态回调函数
        def gui_status_callback(message):
            self.status_text.text(message)
        
        latex_compiler = LaTexCompiler(
            output_latex_dir=transed_latex_dir, 
            latexmk_path=self.latexmk_path,
            compilation_settings=compilation_settings,
            gui_status_callback=gui_status_callback
        )
        pdf_file = latex_compiler.compile()

        sys.stderr = open(os.devnull, 'w')
        self.progress_bar.progress(90)
        sys.stderr = sys.__stderr__
        if pdf_file:
            # 检查是否是瑕疵PDF
            if pdf_file.endswith('_flawed.pdf'):
                sys.stderr = open(os.devnull, 'w')
                self.status_text.text("😔 Generated flawed PDF due to compilation errors.")
                self.progress_bar.progress(100)
                st.warning(f"😔 Generated flawed PDF for {os.path.basename(self.project_dir)} due to compilation errors.")
                time.sleep(2)
                self.process_b.empty()
                self.status_text.empty()
                sys.stderr = sys.__stderr__

                self.log(f"😔 Generated flawed PDF for {os.path.basename(self.project_dir)}.")
                return pdf_file
            else:
                # 完美PDF
                sys.stderr = open(os.devnull, 'w')
                self.status_text.text("✅ Successfully compiled perfect PDF document.")
                self.progress_bar.progress(100)
                st.success(f"✅ Successfully generated perfect PDF for {os.path.basename(self.project_dir)}.")
                time.sleep(2)
                self.process_b.empty()
                self.status_text.empty()
                sys.stderr = sys.__stderr__

                self.log(f"✅ Successfully generated perfect PDF for {os.path.basename(self.project_dir)}.")
                return pdf_file
        else:
            sys.stderr = open(os.devnull, 'w')
            self.status_text.error("❌ Failed to compile PDF document.")
            self.process_b.empty()
            sys.stderr = sys.__stderr__
            return None
        
    def _creat_transed_latex_folder(self, src_dir: str, dest_dir: str) -> str:
        """
        Create a translated folder by copying the source directory.
        """
        if not os.path.isdir(src_dir):
            raise NotADirectoryError(f"The path {src_dir} is not a valid directory.")

        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        shutil.copytree(src_dir, dest_dir)

        return dest_dir
        
    def _patch_problematic_packages(self, main_tex_path: str):
        if not os.path.exists(main_tex_path):
            self.log(f"⚠️  main.tex file not found at {main_tex_path}. Skipping patch.", "warning")
            return
            
        try:
            with open(main_tex_path, 'r', encoding='utf-8') as f:
                content = f.read()

            pattern = r"(\\usepackage(?:\[.*?\])?\{axessibility\})"
            
            if re.search(pattern, content):
                content = re.sub(pattern, r"%\1", content)
                with open(main_tex_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log(f"✅ Patched problematic package 'axessibility' in {main_tex_path}.")

        except Exception as e:
            self.log(f"❌ Error patching file {main_tex_path}: {e}", "error")
