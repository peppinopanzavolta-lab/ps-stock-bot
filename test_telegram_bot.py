from telegram_bot import classify_status, get_page_snapshot, get_status


def test_ps5_pro_current_status():
    status = get_status(
        "https://www.playstation.com/it-it/ps5/ps5-pro/buy-now/"
    )
    assert status == "unavailable"


def test_ps5_slim_disc_current_status():
    status = get_status(
        "https://direct.playstation.com/it-it/buy-consoles/playstation5-console-1-tb"
    )
    assert status == "unavailable"


def test_deal_snapshot_is_not_empty():
    snapshot = get_page_snapshot(
        "https://www.playstation.com/it-it/store/hardware/deals/",
        "deal",
    )
    assert len(snapshot) == 64


def test_status_handles_different_available_wording():
    assert classify_status("Prodotto disponibile - Add to cart") == "available"


def test_status_handles_different_unavailable_wording():
    assert classify_status("Al momento non disponibile") == "unavailable"
