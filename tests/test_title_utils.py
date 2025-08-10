from screendraft2jellyfin.title_utils import generate_query_variants

def test_variants_basic():
    v = set(generate_query_variants("Die Hard with a Vengeance"))
    assert any("Vengeance" in s for s in v)
