from app.pricing_math import price_curve, score_price


def test_score_price_matches_the_written_formula():
    # Price 11 on a current price of 10, drop 10: move 0.1, factor 0.9, demand 90.
    # Horizon 2 and stock 50 sell the whole stock, so nothing is wasted.
    scored = score_price(11, current=10, forecast=100, drop=10, stock=50, cost=4, horizon=2)
    assert scored["demand"] == 90
    assert scored["sellable"] == 50
    assert scored["wasted"] == 0
    assert scored["profit"] == 350
    assert scored["below_cost"] is False


def test_score_price_counts_unsold_stock_as_a_total_loss():
    # Price 15, move 0.5, drop 10, factor 0.5, demand 50. Two weeks sell 100 of 500.
    scored = score_price(15, current=10, forecast=100, drop=10, stock=500, cost=4, horizon=2)
    assert scored["demand"] == 50
    assert scored["sellable"] == 100
    assert scored["wasted"] == 400
    assert scored["profit"] == -500


def test_curve_point_equals_score_price_and_is_not_capped():
    curve = price_curve(
        current=10,
        forecast=100,
        drop=10,
        stock=500,
        cost=4,
        horizon=2,
        anchors=[6],
    )
    point = next(item for item in curve if item["price"] == 6)
    assert point == score_price(6, current=10, forecast=100, drop=10, stock=500, cost=4, horizon=2)
    # 6 is 40% below 10. A capped suggestion would have stopped at 8.
    assert point["price"] < 8
