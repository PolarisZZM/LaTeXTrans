from typing import Dict, Any, List
from src.agents.tool_agents.base_tool_agent import BaseToolAgent
from pathlib import Path
import sys
import os
import shutil
import re

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

    def execute(self) -> Any:
        
        self.log(f"🤖💬 Start generating for project...⏳: {os.path.basename(self.project_dir)}.")

        from src.formats.latex.compile import LaTexCompiler
        from src.formats.latex.reconstruct import LatexConstructor

        sections = self.read_file(Path(self.output_dir, "sections_map.json"), "json")
        captions = self.read_file(Path(self.output_dir, "captions_map.json"), "json")
        envs = self.read_file(Path(self.output_dir, "envs_map.json"), "json")
        newcommands = self.read_file(Path(self.output_dir, "newcommands_map.json"), "json")
        inputs = self.read_file(Path(self.output_dir, "inputs_map.json"), "json")
        
        # Note: The original _creat_transed_latex_folder returns the parent dir of the project,
        # but the compilation happens inside the project dir. Let's adjust slightly.
        project_name = os.path.basename(self.project_dir)
        transed_project_dir = os.path.join(self.output_dir, project_name)
        transed_latex_dir = self._creat_transed_latex_folder(self.project_dir, transed_project_dir)

        latex_constructor = LatexConstructor(
                                sections=sections,
                                captions=captions,
                                envs=envs,
                                inputs=inputs,
                                newcommands=newcommands,
                                output_latex_dir=transed_latex_dir
                             )
        latex_constructor.construct()

        self._patch_problematic_packages(os.path.join(transed_latex_dir, "main.tex"))

        latex_compiler = LaTexCompiler(
            output_latex_dir=transed_latex_dir,
            latexmk_path=self.latexmk_path 
        )
        pdf_file = latex_compiler.compile()
        if pdf_file:
            if "_flawed.pdf" in pdf_file:
                self.log(f"⚠️✅  Successfully generated a flawed PDF for {os.path.basename(self.project_dir)}. Please check the output for potential issues.")
            else:
                self.log(f"✅ Successfully generated for {os.path.basename(self.project_dir)}.")
            return pdf_file
        else:
            self.log(f"❌ Failed to generate PDF for {os.path.basename(self.project_dir)}.", "error")
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
