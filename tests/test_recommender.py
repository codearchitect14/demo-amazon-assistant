from recommender.recommender import recommend_products


def test_recommend_products():
    results = recommend_products("face moisturizer", {})
    assert isinstance(results, list)
