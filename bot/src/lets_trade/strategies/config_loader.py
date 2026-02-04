"""전략 설정 로더"""

import json
import os
from pathlib import Path
from typing import Optional

import yaml

from .base import StrategyConfig


class StrategyConfigLoader:
    """전략 설정 파일 로더"""

    @staticmethod
    def load_yaml(path: str | Path) -> StrategyConfig:
        """YAML 파일에서 전략 설정 로드"""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return StrategyConfigLoader._parse_config(data)

    @staticmethod
    def load_json(path: str | Path) -> StrategyConfig:
        """JSON 파일에서 전략 설정 로드"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return StrategyConfigLoader._parse_config(data)

    @staticmethod
    def load(path: str | Path) -> StrategyConfig:
        """파일 확장자에 따라 자동으로 로드"""
        path = Path(path)
        if path.suffix in [".yaml", ".yml"]:
            return StrategyConfigLoader.load_yaml(path)
        elif path.suffix == ".json":
            return StrategyConfigLoader.load_json(path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {path.suffix}")

    @staticmethod
    def save_yaml(config: StrategyConfig, path: str | Path) -> None:
        """전략 설정을 YAML 파일로 저장"""
        data = StrategyConfigLoader._config_to_dict(config)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    @staticmethod
    def save_json(config: StrategyConfig, path: str | Path) -> None:
        """전략 설정을 JSON 파일로 저장"""
        data = StrategyConfigLoader._config_to_dict(config)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _parse_config(data: dict) -> StrategyConfig:
        """딕셔너리를 StrategyConfig로 변환"""
        return StrategyConfig(
            name=data.get("name", "Unnamed"),
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            symbols=data.get("symbols", []),
            max_investment=data.get("max_investment", 1_000_000),
            max_loss_rate=data.get("max_loss_rate", 5.0),
            take_profit_rate=data.get("take_profit_rate", 10.0),
            is_active=data.get("is_active", True),
        )

    @staticmethod
    def _config_to_dict(config: StrategyConfig) -> dict:
        """StrategyConfig를 딕셔너리로 변환"""
        return {
            "name": config.name,
            "description": config.description,
            "parameters": config.parameters,
            "symbols": config.symbols,
            "max_investment": config.max_investment,
            "max_loss_rate": config.max_loss_rate,
            "take_profit_rate": config.take_profit_rate,
            "is_active": config.is_active,
        }


class StrategyManager:
    """전략 관리자"""

    def __init__(self, config_dir: str | Path = "strategies"):
        self.config_dir = Path(config_dir)
        self.strategies: dict[str, StrategyConfig] = {}

    def load_all(self) -> dict[str, StrategyConfig]:
        """설정 디렉토리의 모든 전략 로드"""
        self.strategies = {}

        if not self.config_dir.exists():
            return self.strategies

        for path in self.config_dir.glob("*.yaml"):
            try:
                config = StrategyConfigLoader.load_yaml(path)
                self.strategies[config.name] = config
            except Exception as e:
                print(f"전략 로드 실패 ({path}): {e}")

        for path in self.config_dir.glob("*.json"):
            try:
                config = StrategyConfigLoader.load_json(path)
                self.strategies[config.name] = config
            except Exception as e:
                print(f"전략 로드 실패 ({path}): {e}")

        return self.strategies

    def get(self, name: str) -> Optional[StrategyConfig]:
        """전략 설정 조회"""
        return self.strategies.get(name)

    def get_active_strategies(self) -> list[StrategyConfig]:
        """활성화된 전략 목록"""
        return [s for s in self.strategies.values() if s.is_active]

    def save(self, config: StrategyConfig, format: str = "yaml") -> Path:
        """전략 설정 저장"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{config.name.lower().replace(' ', '_')}.{format}"
        path = self.config_dir / filename

        if format == "yaml":
            StrategyConfigLoader.save_yaml(config, path)
        else:
            StrategyConfigLoader.save_json(config, path)

        self.strategies[config.name] = config
        return path
