import numpy as np
import pandas as pd
import pytest

import momentum_backtest.data as data_module
from momentum_backtest.data import _validate_prices, load_prices, synthetic_prices


def test_synthetic_prices_are_reproducible_and_positive() -> None:
    first = synthetic_prices(n_assets=3, n_days=10, seed=7)
    second = synthetic_prices(n_assets=3, n_days=10, seed=7)

    pd.testing.assert_frame_equal(first, second)
    assert first.shape == (10, 3)
    assert first.gt(0.0).all().all()


def test_price_validation_rejects_partial_missing_data() -> None:
    prices = pd.DataFrame(
        {"A": [100.0, np.nan], "B": [50.0, 51.0]},
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    )

    with pytest.raises(ValueError, match="missing observations"):
        _validate_prices(prices, ["A", "B"])


def _multiindex_download_response(tickers: list[str], dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Mimic yfinance's actual (Price, Ticker) MultiIndex column response, verified
    empirically against yfinance 1.5.x - the real shape even for a single ticker."""
    columns = pd.MultiIndex.from_product(
        [["Close", "High", "Low", "Open", "Volume"], tickers], names=["Price", "Ticker"]
    )
    data = np.tile(np.arange(1.0, len(dates) + 1.0).reshape(-1, 1), (1, len(columns)))
    return pd.DataFrame(data, index=dates, columns=columns)


def test_load_prices_parses_multiindex_response_and_caches(tmp_path, mocker) -> None:
    mocker.patch.object(data_module, "CACHE_DIR", tmp_path)
    dates = pd.bdate_range("2024-01-01", periods=5)
    response = _multiindex_download_response(["A", "B"], dates)
    download = mocker.patch("yfinance.download", return_value=response)

    prices = load_prices(["A", "B"], "2024-01-01", "2024-01-08")

    assert download.call_count == 1
    assert list(prices.columns) == ["A", "B"]
    assert len(prices) == 5
    cache_files = list(tmp_path.glob("prices_*.csv"))
    assert len(cache_files) == 1


def test_load_prices_second_call_hits_cache_not_network(tmp_path, mocker) -> None:
    mocker.patch.object(data_module, "CACHE_DIR", tmp_path)
    dates = pd.bdate_range("2024-01-01", periods=5)
    response = _multiindex_download_response(["A"], dates)
    download = mocker.patch("yfinance.download", return_value=response)

    load_prices(["A"], "2024-01-01", "2024-01-08")
    load_prices(["A"], "2024-01-01", "2024-01-08")

    assert download.call_count == 1  # second call must be served from the cache


def test_load_prices_different_universe_bypasses_stale_cache(tmp_path, mocker) -> None:
    mocker.patch.object(data_module, "CACHE_DIR", tmp_path)
    dates = pd.bdate_range("2024-01-01", periods=5)
    download = mocker.patch(
        "yfinance.download",
        side_effect=[
            _multiindex_download_response(["A"], dates),
            _multiindex_download_response(["A", "B"], dates),
        ],
    )

    load_prices(["A"], "2024-01-01", "2024-01-08")
    load_prices(["A", "B"], "2024-01-01", "2024-01-08")

    assert download.call_count == 2  # different universe must not reuse the A-only cache


def test_load_prices_rejects_response_without_close(tmp_path, mocker) -> None:
    mocker.patch.object(data_module, "CACHE_DIR", tmp_path)
    dates = pd.bdate_range("2024-01-01", periods=5)
    columns = pd.MultiIndex.from_product([["Open"], ["A"]], names=["Price", "Ticker"])
    response = pd.DataFrame(1.0, index=dates, columns=columns)
    mocker.patch("yfinance.download", return_value=response)

    with pytest.raises(ValueError, match="adjusted close"):
        load_prices(["A"], "2024-01-01", "2024-01-08")


def test_load_prices_discards_and_redownloads_a_corrupted_cache_file(tmp_path, mocker) -> None:
    mocker.patch.object(data_module, "CACHE_DIR", tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    dates = pd.bdate_range("2024-01-01", periods=5)
    cache_path = data_module._cache_path(["A"], "2024-01-01", "2024-01-08")
    cache_path.write_text("not,valid,csv,for,this,schema\n1,2\n")
    download = mocker.patch(
        "yfinance.download", return_value=_multiindex_download_response(["A"], dates)
    )

    prices = load_prices(["A"], "2024-01-01", "2024-01-08")

    assert download.call_count == 1
    assert list(prices.columns) == ["A"]
