"""Simple entry point to verify the uv environment is working."""

import sys


def main():
    print("✓ Python environment active")
    print(f"  Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Test core dependencies
    try:
        import aiohttp
        import prefect
        import prefect_email

        print(f"✓ All packages installed")
    except ImportError as e:
        print(f"✗ Packages not installed: {e}")

    print("\nEnvironment ready!")


if __name__ == "__main__":
    main()
