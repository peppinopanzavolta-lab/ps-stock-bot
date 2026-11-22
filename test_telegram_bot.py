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


def test_status_handles_exact_unavailable_purchase_wording():
    assert classify_status("Non disponibile per l'acquisto") == "unavailable"






def test_ps5_slim_official_page_current_status():
    status = get_status(
        "https://www.playstation.com/it-it/ps5/1-tb-disc/"
    )
    assert status == "unavailable"


def test_ps5_bundle_pages_current_status():
    urls = [
        "https://www.playstation.com/it-it/ps5/1-tb-disc/product/ea-sports-fc-26-bundle/",
        "https://www.playstation.com/it-it/ps5/1-tb-disc/product/fortnite-flowering-chaos-bundle/",
        "https://www.playstation.com/it-it/ps5/1-tb-disc/product/two-dualsense-wireless-controllers-bundle/",
    ]
    for url in urls:
        assert get_status(url) in {"available", "unavailable", "unknown"}
