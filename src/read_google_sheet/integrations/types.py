"""Core types for Google Sheets integration."""

from dataclasses import dataclass

from polars_result import Err, Ok, Result

# from read_google_sheet.core import exceptions

# ============================================================================
# Type Aliases
# ============================================================================

type DataSource = dict[str, str]
type SheetConfigs = dict[str, "SheetConfig"]


# ============================================================================
# Validated SheetId
# ============================================================================


class SheetId(str):
    """
    Validated Google Sheet ID.
    Always 44 characters, alphanumeric with hyphens/underscores only.
    """

    def __new__(cls, value: str) -> "SheetId":
        if not isinstance(value, str):
            raise TypeError(f"SheetId must be str, got {type(value)}")

        value = value.strip()

        if not value:
            raise ValueError("SheetId cannot be empty")

        if len(value) != 44:
            raise ValueError(f"SheetId must be 44 characters, got {len(value)}")

        if not all(c.isalnum() or c in "-_" for c in value):
            raise ValueError(
                "SheetId can only contain alphanumeric characters, hyphens, or underscores"
            )

        return str.__new__(cls, value)

    @classmethod
    def validate(cls, value: str) -> Result["SheetId", Exception]:
        """Validate and create SheetId, returning Result."""
        if not isinstance(value, str):
            return Err(TypeError(f"SheetId must be str, got {type(value)}"))

        value = value.strip()

        if not value:
            return Err(ValueError("SheetId cannot be empty"))

        if len(value) != 44:
            return Err(ValueError(f"SheetId must be 44 characters, got {len(value)}"))

        if not all(c.isalnum() or c in "-_" for c in value):
            return Err(
                ValueError(
                    "SheetId can only contain alphanumeric characters, hyphens, or underscores"
                )
            )

        return Ok(cls(value))

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Quick boolean check if a string is a valid SheetId."""
        return cls.validate(value).is_ok()


# ============================================================================
# Sheet Configuration
# ============================================================================


@dataclass(frozen=True, slots=True)
class SheetConfig:
    """Configuration for a single Google Sheet."""

    sheet_id: SheetId
    sheet_name: str

    def __post_init__(self) -> None:
        if not isinstance(self.sheet_id, SheetId):
            raise TypeError(f"sheet_id must be SheetId, got {type(self.sheet_id)}")
        if not isinstance(self.sheet_name, str):
            raise TypeError(f"sheet_name must be str, got {type(self.sheet_name)}")
        if not self.sheet_name.strip():
            raise ValueError("sheet_name cannot be empty")

    @classmethod
    def create(cls, sheet_id: str, sheet_name: str) -> Result["SheetConfig", Exception]:
        """Create SheetConfig with validation. Preferred over direct instantiation."""

        def validate_name(validated_id: SheetId) -> Result["SheetConfig", Exception]:
            if not isinstance(sheet_name, str):
                return Err(TypeError(f"sheet_name must be str, got {type(sheet_name)}"))
            if not sheet_name.strip():
                return Err(ValueError("sheet_name cannot be empty"))
            return Ok(cls(sheet_id=validated_id, sheet_name=sheet_name))

        return SheetId.validate(sheet_id).and_then(validate_name)

    def to_dict(self) -> DataSource:
        return {"sheet_id": str(self.sheet_id), "sheet_name": self.sheet_name}
