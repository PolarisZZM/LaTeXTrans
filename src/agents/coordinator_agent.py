import os
import shutil
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys
import asyncio

base_dir = os.getcwd()
sys.path.append(base_dir)

from .tool_agents.base_tool_agent import BaseToolAgent
from .tool_agents.parser_agent import ParserAgent
from .tool_agents.translator_agent import TranslatorAgent
from .tool_agents.generator_agent import GeneratorAgent
from .tool_agents.validator_agent import ValidatorAgent
import gc


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
        self.source_language = config.get("source_language", "en")
        self.project_dir = project_dir  # Project path for parsing
        self.output_dir = output_dir  # Output directory for parsed files
        self.loop = asyncio.new_event_loop()  # 添加事件循环
        self.mode = config.get("mode", 0)

    def run_async(self, coro):
        """在已有事件循环中运行异步协程"""
        return self.loop.run_until_complete(coro)

    async def workflow_latextrans_async(self) -> None:
        """
        initializes the tool agent based on the provided agent name key.
        """
        base_name = os.path.basename(self.project_dir)
        transed_project_dir = os.path.join(self.output_dir, f"{self.target_language}_{base_name}")

        os.makedirs(transed_project_dir, exist_ok=True)

        parser_agent = ParserAgent(config=self.config,
                                   project_dir=self.project_dir,
                                   output_dir=transed_project_dir)
        parser_agent.execute()  # 假设ParserAgent仍然是同步的

        translator_agent = TranslatorAgent(config=self.config,
                                           project_dir=self.project_dir,
                                           output_dir=transed_project_dir,
                                           trans_mode=self.mode)
        await translator_agent.execute()  # 异步调用
        validator_agent = ValidatorAgent(config=self.config,
                                            project_dir=self.project_dir,
                                            output_dir=transed_project_dir)
        errors_report = validator_agent.execute()
        MAX_RETRIES = 3
        retry_count = 0
        if errors_report:
            translator_agent.trans_mode = 1

        while errors_report and retry_count < MAX_RETRIES: # 3 times
            translator_agent.errors_report = errors_report
            await translator_agent.execute(error_retry_count=retry_count, Maxtry=MAX_RETRIES)
            errors_report = validator_agent.execute(errors_report)
            retry_count += 1

        generator_agent = GeneratorAgent(config=self.config,
                                         project_dir=self.project_dir,
                                         output_dir=transed_project_dir)
        try:
        
            PDF_file_path = generator_agent.execute()
        except Exception as e:
            print(f"🤖🚧 {self.name}: Failed to translated {os.path.basename(self.project_dir)}.{e}")
            return
        
        
        
        if PDF_file_path:
            new_PDF_path = os.path.join(os.path.dirname(PDF_file_path), f"{self.target_language}_{base_name}.pdf")
            shutil.move(PDF_file_path, new_PDF_path)
            print(f"🤖🎉 {self.name}: Successfully translated {os.path.basename(self.project_dir)} to {new_PDF_path}.")
            return new_PDF_path
        else:
            print(f"🤖🚧 {self.name}: Failed to translated {os.path.basename(self.project_dir)}.")

    # def workflow_latextrans(self) -> None:
    #     """
    #     initializes the tool agent based on the provided agent name key.
    #     """
    #     # 创建新的事件循环（如果还没有）
    #     if not hasattr(self, 'loop'):
    #         self.loop = asyncio.new_event_loop()
    #         asyncio.set_event_loop(self.loop)
    #
    #     # 运行异步工作流
    #     self.loop.run_until_complete(self.workflow_latextrans_async())

    def workflow_latextrans(self) -> None:
        """
        初始化工具代理并执行LaTeX转换工作流（带事件循环安全管理）
        """
        # ---- 安全启动机制 ----
        if hasattr(self, 'loop') and not self.loop.is_closed():
            self.loop.close()  # 关闭残留循环

        # 创建隔离的事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            # ---- 核心工作流执行 ----
            self.loop.run_until_complete(self.workflow_latextrans_async())

        finally:
            # ---- 安全关闭序列 ----
            # 1. 完成所有异步资源回收
            if tasks := asyncio.all_tasks(self.loop):
                self.loop.run_until_complete(
                    asyncio.gather(*tasks, return_exceptions=True)
                )

            # 2. 特别处理Windows的异步I/O回收
            if sys.platform == "win32":
                self.loop.run_until_complete(
                    self.loop.shutdown_asyncgens()
                )

            # 3. 安全关闭循环（防止__del__触发访问）
            self.loop.run_until_complete(self.loop.shutdown_default_executor())
            # self.loop.close()
            # del self.loop  # 解除引用









