# Nexora AI

Production-grade Python platform for AI-powered content research, generation, scheduling, and multi-channel publishing (Facebook, YouTube).

## Project Structure

```
Nexora-AI-Pro/
├── main.py                 # Application entry point
├── config.py               # Central configuration loader
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
│
├── research/               # Topic and trend research
├── content/                # Text and copy generation
├── image_generation/       # Image asset creation
├── scheduler/              # Posting and job scheduling
├── analytics/              # Performance tracking and reporting
├── facebook/               # Facebook integration
├── youtube/                # YouTube integration
├── config/                 # Shared constants and config helpers
├── utils/                  # Shared utilities (logging, helpers)
├── logs/                   # Runtime log output (gitignored)
├── data/                   # Local data storage (gitignored)
└── tests/                  # Test suite
```

Each module directory contains an `__init__.py` that documents its intended responsibility. The `config/` folder holds helper modules (e.g. `constants.py`); root-level `config.py` is the settings loader. Business logic is not implemented yet.

## Getting Started

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   # source .venv/bin/activate   # macOS / Linux
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy the environment template and fill in your values:

   ```bash
   copy .env.example .env        # Windows
   # cp .env.example .env        # macOS / Linux
   ```

4. Run the application:

   ```bash
   python main.py
   ```

## Environment Variables

See `.env.example` for all supported settings. Never commit a real `.env` file.

## Development

- Place unit and integration tests under `tests/`.
- Write logs to `logs/` at runtime.
- Store local datasets, caches, and exports under `data/`.

## License

Proprietary — Nexora AI.
