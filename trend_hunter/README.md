# Trend Hunter

Production module for discovering trending topics across multiple external
sources. Trend Hunter follows clean architecture: domain models sit at the
center, provider adapters depend inward on interfaces, and the service layer
orchestrates async discovery without knowing source-specific details.

## Architecture

```
trend_hunter/
├── domain/           # Pydantic models and enumerations (no I/O)
├── interfaces/       # Provider port (Protocol + ABC)
├── providers/        # Provider registry; adapters register at startup
├── services/         # TrendHunterService — concurrent fetch + aggregation
├── config/           # TREND_HUNTER_* environment settings
├── di/               # TrendHunterContainer composition root
├── infrastructure/   # Logging setup
└── exceptions/       # Typed error hierarchy
```

Data flows outward from providers → service → caller:

1. Caller builds a ``TrendHunterRequest`` with an optional ``TrendQuery``.
2. ``TrendHunterService.discover`` resolves eligible providers from the registry.
3. Providers are queried concurrently (bounded by ``fetch_concurrency``).
4. Results are deduplicated, sorted, and returned as ``TrendHunterResponse``.

## Supported provider types (Phase 1)

| Provider        | Enum value       | Status        |
|-----------------|------------------|---------------|
| Google Trends   | `google_trends`  | Not yet built |
| Reddit          | `reddit`         | Not yet built |
| News API        | `news_api`       | Not yet built |
| RSS feeds       | `rss`            | Not yet built |
| YouTube         | `youtube`        | Not yet built |

Phase 1 delivers the contract and wiring only. Each provider will be added as
an adapter class extending ``BaseTrendProvider`` and registered on the
container at application startup.

## Configuration

Trend Hunter reads from the project ``.env`` file using the
``TREND_HUNTER_`` prefix:

```env
TREND_HUNTER_ENABLED_PROVIDERS=google_trends,reddit,rss
TREND_HUNTER_SKIP_UNCONFIGURED=true
TREND_HUNTER_FETCH_CONCURRENCY=5
TREND_HUNTER_REQUEST_TIMEOUT_SECONDS=30
TREND_HUNTER_LOG_LEVEL=INFO
TREND_HUNTER_LOG_TO_FILE=true
TREND_HUNTER_REDDIT_CLIENT_ID=
TREND_HUNTER_REDDIT_CLIENT_SECRET=
TREND_HUNTER_NEWS_API_KEY=
TREND_HUNTER_YOUTUBE_API_KEY=
TREND_HUNTER_RSS_FEED_URLS=
```

## Usage

```python
import asyncio

from trend_hunter import TrendHunterRequest, TrendQuery, create_container

async def main() -> None:
    container = create_container()
    # Register provider adapters here once they are implemented:
    # container.register_provider(MyGoogleTrendsProvider(settings=container.settings))

    response = await container.service.discover(
        TrendHunterRequest(query=TrendQuery(keywords=("artificial intelligence",)))
    )
    print(f"Discovered {response.total_items} trend(s).")

asyncio.run(main())
```

## Implementing a provider adapter

1. Subclass ``BaseTrendProvider`` in ``trend_hunter/providers/<source>.py``.
2. Implement ``provider_type``, ``is_configured``, and ``fetch_trends``.
3. Map upstream API responses to ``TrendItem`` instances inside ``fetch_trends``.
4. Register the adapter during bootstrap:

```python
container.register_provider(GoogleTrendsProvider(settings=container.settings))
```

5. Raise ``ProviderFetchError`` only for unrecoverable configuration mistakes;
   return ``TrendResult(errors=(...))`` for expected API failures.

## Testing

Unit tests should construct a ``TrendHunterContainer`` with in-memory provider
fakes that implement ``TrendProvider``. The service layer accepts any object
satisfying the protocol, so tests never require live network access.
