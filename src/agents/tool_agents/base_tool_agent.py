from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import json
import yaml
import toml
from pathlib import Path


class BaseToolAgent(ABC):
    """
    Abstract base class for all tool agents in the multi-agent translation system.

    Each tool agent is responsible for a specific task in the translation workflow,
    such as parsing, translating, refining, or validating documents.
    """

    def __init__(
        self,
        agent_name: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initializes the BaseToolAgent.

        Args:
            agent_name (str): The unique name of this agent (e.g., "ParserAgent", "TranslatorAgent").
            config (Optional[Dict[str, Any]]): Agent-specific configuration parameters
                                               loaded from the TOML files. Defaults to None.
        """
        self.agent_name = agent_name
        self.config = config if config is not None else {}
        
    def log(self, message: str, level: str = "info"):
        """
        Logs messages at different levels (info, debug, warning, error).

        Args:
            message (str): The message to log.
            level (str): The logging level. Defaults to "info".
        """
        if level == "info":
            print(f"[{self.agent_name}] [INFO] {message}")
        elif level == "debug":
            print(f"[{self.agent_name}] [DEBUG] {message}")
        elif level == "warning":
            print(f"[{self.agent_name}] [WARNING] {message}")
        elif level == "error":
            print(f"[{self.agent_name}] [ERROR] {message}")
        else:
            raise ValueError(f"Unknown log level: {level}")

    @abstractmethod
    def execute(self, data: Any, **kwargs: Any) -> Any:
        """
        Executes the core task of the agent.

        This method must be implemented by all concrete tool agent subclasses.
        The input `data` and the returned `Any` type will vary depending on the
        specific agent's role in the workflow (e.g., file path, text string,
        parsed document object, translation result).
        """
        raise NotImplementedError(f"{self.__class__.__name__}.execute() must be implemented.")

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value for the agent.
        If the key does not exist, returns the provided default value.
        """
        return self.config.get(key, default)
    
    def read_file(self, file_path: str, file_format: str) -> str:
        """
        Reads a file and returns its content.
        """
        if file_format == "json":
            with open(file_path, "r", encoding='utf-8') as f:
                return json.load(f)
        elif file_format == "yaml":
            with open(file_path, "r", encoding='utf-8') as f:
                return yaml.load(f)
        elif file_format == "toml":
            with open(file_path, "r", encoding='utf-8') as f:
                return toml.load(f)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
    def save_file(self, file_path: str, file_format: str, data: Any):
        """
        Saves data to a file.
        """
        if file_format == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)   
        elif file_format == "yaml":
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f)
        elif file_format == "toml":
            with open(file_path, 'w', encoding='utf-8') as f:
                toml.dump(data, f)


