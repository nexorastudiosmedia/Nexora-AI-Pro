"""
Nexora AI — application entry point.

Orchestrates module startup. Business logic lives in package subdirectories.
"""

from config import get_settings


def main() -> None:
    """Bootstrap Nexora AI. Extend this as modules are implemented."""
    settings = get_settings()
    print(f"{settings.app_name} — environment: {settings.app_env}")


if __name__ == "__main__":
    main()
