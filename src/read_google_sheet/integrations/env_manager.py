"""Environment variable management for Google Sheets configuration."""

from pathlib import Path

from polars_result import Err, Ok, Result
from src.read_google_sheet.core import exceptions
from src.read_google_sheet.integrations.dotenv_loader import DotenvLoader
from src.read_google_sheet.integrations.types import DataSource, SheetConfig, SheetConfigs, SheetId


class SheetEnvironmentManager:
    """Handles environment variable operations for Google Sheets."""

    @staticmethod
    def _parse_env_file(env_path: Path) -> Result[DataSource, Exception]:
        """Parse .env file and return dict of variable name -> value."""
        if not env_path.exists():
            return Err(exceptions.ConfigurationError(f"File {env_path} does not exist"))

        if not env_path.is_file():
            return Err(exceptions.ConfigurationError(f"{env_path} is not a file"))

        def read_lines() -> Result[list[str], Exception]:
            try:
                with open(env_path, encoding="utf-8") as f:
                    return Ok(f.readlines())
            except PermissionError:
                return Err(exceptions.ConfigurationError(f"Permission denied: {env_path}"))
            except UnicodeDecodeError:
                return Err(exceptions.ConfigurationError(f"Invalid encoding: {env_path}"))
            except exceptions.EnvError as e:
                return Err(exceptions.EnvError(f"Error reading {env_path}: {e}"))

        lines_result = read_lines()
        if not lines_result.is_ok():
            return lines_result  # type: ignore

        env_vars: DataSource = {}
        for line in lines_result.unwrap():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                var_name, value = line.split("=", 1)
                env_vars[var_name.strip()] = value.strip().strip("\"'")

        return Ok(env_vars)

    @staticmethod
    def _extract_sheet_prefixes(env_vars: DataSource) -> set[str]:
        """Extract sheet prefixes from environment variable names."""
        prefixes: set[str] = set()
        for var_name in env_vars:
            if var_name.endswith("_ID") or var_name.endswith("_NAME"):
                prefix = var_name.rsplit("_", 1)[0]
                prefixes.add(prefix)
        return prefixes

    @classmethod
    def _build_sheet_config(
        cls, prefix: str, env_vars: DataSource
    ) -> Result[tuple[str, SheetConfig], Exception]:
        """Build config for a single sheet prefix."""
        sheet_id_var = f"{prefix}_ID"
        sheet_name_var = f"{prefix}_NAME"

        if sheet_id_var not in env_vars:
            return Err(exceptions.ConfigurationError(f"Missing {sheet_id_var}"))
        if sheet_name_var not in env_vars:
            return Err(exceptions.ConfigurationError(f"Missing {sheet_name_var}"))

        def add_prefix(config: SheetConfig) -> Result[tuple[str, SheetConfig], Exception]:
            return Ok((prefix.lower(), config))

        return SheetConfig.create(env_vars[sheet_id_var], env_vars[sheet_name_var]).and_then(
            add_prefix
        )

    @classmethod
    def load_sheet_configs(cls, env_file: str = ".env") -> Result[SheetConfigs, Exception]:
        """Load all sheet configurations from .env file."""
        env_path = Path(env_file)

        def parse_to_configs(env_vars: DataSource) -> Result[SheetConfigs, Exception]:
            prefixes = cls._extract_sheet_prefixes(env_vars)

            if not prefixes:
                return Err(
                    exceptions.ConfigurationError(f"No sheet configurations found in {env_file}")
                )

            configs: SheetConfigs = {}
            for prefix in prefixes:
                config_result = cls._build_sheet_config(prefix, env_vars)
                if config_result.is_ok():
                    config_name, config_data = config_result.unwrap()
                    configs[config_name] = config_data

            if not configs:
                return Err(
                    exceptions.ConfigurationError(
                        f"No valid sheet configurations found in {env_file}"
                    )
                )

            return Ok(configs)

        return (
            DotenvLoader.load_dotenv(env_path)
            .and_then(lambda _: cls._parse_env_file(env_path))
            .and_then(parse_to_configs)
        )

    @classmethod
    def save_sheet_config(
        cls, config_name: str, sheet_id: str, sheet_name: str, env_file: str = ".env"
    ) -> Result[str, Exception]:
        """Save sheet configuration to .env file."""
        sheet_id_result = SheetId.validate(sheet_id)
        if not sheet_id_result.is_ok():
            return Err(
                exceptions.ConfigurationError(f"Invalid sheet ID: {sheet_id_result.unwrap_err()}")
            )

        if not sheet_name.strip():
            return Err(exceptions.ConfigurationError("Sheet name cannot be empty"))

        env_path = Path(env_file)
        if not env_path.exists():
            env_path.touch()

        config_upper = config_name.upper()
        sheet_id_var = f"{config_upper}_ID"
        sheet_name_var = f"{config_upper}_NAME"

        def save_id(result1: tuple[bool | None, str, str]) -> Result[str, Exception]:
            success1, *_ = result1
            if not success1:
                return Err(exceptions.EnvError(f"Failed to save {sheet_id_var}"))

            def check_name_save(result2: tuple[bool | None, str, str]) -> Result[str, Exception]:
                success2, *_ = result2
                if success2:
                    return Ok(f"Sheet config '{config_name}' saved to {env_file}")
                return Err(exceptions.EnvError(f"Failed to save {sheet_name_var}"))

            return DotenvLoader.set_key(str(env_path), sheet_name_var, sheet_name).and_then(
                check_name_save
            )

        return DotenvLoader.set_key(str(env_path), sheet_id_var, sheet_id).and_then(save_id)

    @classmethod
    def get_sheet_config(
        cls, config_name: str, env_file: str = ".env"
    ) -> Result[SheetConfig, Exception]:
        """Get a specific sheet configuration by name."""

        def extract_config(configs: SheetConfigs) -> Result[SheetConfig, Exception]:
            config_key = config_name.lower()
            if config_key in configs:
                return Ok(configs[config_key])
            return Err(
                exceptions.ConfigurationError(
                    f"Sheet config '{config_name}' not found in {env_file}"
                )
            )

        return cls.load_sheet_configs(env_file).and_then(extract_config)
