from telegram_bot import get_page_snapshot, get_status


def test_ps5_pro_current_status():
    status = get_status(
        "https://www.playstation.com/it-it/ps5/ps5-pro/buy-now/"
    )
    assert status == "unavailable"


def test_deal_snapshot_is_not_empty():
    snapshot = get_page_snapshot(
        "https://www.playstation.com/it-it/store/hardware/deals/",
        "deal",
    )
    assert len(snapshot) == 64
