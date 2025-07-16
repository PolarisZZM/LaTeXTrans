import os
import shutil
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys

base_dir = os.getcwd()
sys.path.append(base_dir)

from .tool_agents.base_tool_agent import BaseToolAgent
from .tool_agents.parser_agent import ParserAgent
from .tool_agents.translator_agent import TranslatorAgent
from .tool_agents.generator_agent import GeneratorAgent
from .tool_agents.validator_agent import ValidatorAgent 


class CoordinatorAgent:
    """
    The main orchestrator agent for the translation system. It coordinates the workflow of various tool agents based on document format
    and configuration.
    """

    def __init__(self, 
                 config: Dict[str, Any],
                 project_dir: str = None,
                 output_dir: Optional[str] = None,
                 latexmk_path: str = None  # <--- 新增参数
                 ):
        """
        Initializes the CoordinatorAgent.
        """
        self.config = config
        self.name = config.get("sys_name", "LaTeXTrans")
        self.target_language = config.get("target_language", "ch")
        self.project_dir = project_dir  # Project path for parsing
        self.output_dir = output_dir  # Output directory for parsed files
        self.latexmk_path = latexmk_path # <--- 存储路径

    def workflow_latextrans(self) -> None:
        """
        initializes the tool agent based on the provided agent name key.
        """
        base_name = os.path.basename(self.project_dir)
        transed_project_dir = os.path.join(self.output_dir, f"{self.target_language}_{base_name}")

        os.makedirs(transed_project_dir, exist_ok=True)  

        parser_agent = ParserAgent(config=self.config, 
                                    project_dir=self.project_dir,
                                    output_dir=transed_project_dir)
        parser_agent.execute()
        translator_agent = TranslatorAgent(config=self.config,
                                            project_dir=self.project_dir,
                                            output_dir=transed_project_dir,
                                            trans_mode=0)
        translator_agent.execute()
        
        # ... (retry logic is commented out, keeping it as is) ...

        # 将路径传递给 GeneratorAgent
        generator_agent = GeneratorAgent(config=self.config,
                                          project_dir=self.project_dir,
                                          output_dir=transed_project_dir,
                                          latexmk_path=self.latexmk_path) # <--- 传递路径
        try:
            PDF_file_path = generator_agent.execute()
        except Exception as e:
            print(f"🤖🚧 {self.name}: Failed to translated {os.path.basename(self.project_dir)}.{e}")
            return

        if PDF_file_path:
            # Note: The original code had a small bug here, moving the PDF to a file named after the folder.
            # The destination should probably be inside the translated project directory.
            # Keeping original logic but this might be something to review.
            new_PDF_path = os.path.join(os.path.dirname(PDF_file_path), f"{self.target_language}_{base_name}.pdf")
            shutil.move(PDF_file_path, new_PDF_path)
            print(f"🤖🎉 {self.name}: Successfully translated {os.path.basename(self.project_dir)} to {new_PDF_path}.")
        else:
            print(f"🤖🚧 {self.name}: Failed to translated {os.path.basename(self.project_dir)}.")