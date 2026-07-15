import numpy as np
import pandas as pd
import pytest

from src.data import _validate_prices, synthetic_prices


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
