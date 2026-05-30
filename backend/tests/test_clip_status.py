from app.services.clip_status import ClipStatus, aggregate_clip_status


def test_empty_clips():
    assert aggregate_clip_status(set()) == ClipStatus.READY


def test_all_ready():
    assert aggregate_clip_status({"ready"}) == ClipStatus.READY


def test_all_failed():
    assert aggregate_clip_status({"failed"}) == ClipStatus.FAILED


def test_uploading_takes_priority():
    assert aggregate_clip_status({"uploading", "ready"}) == ClipStatus.UPLOADING


def test_processing_over_uploaded():
    assert aggregate_clip_status({"processing", "uploaded"}) == ClipStatus.PROCESSING


def test_uploaded_over_ready():
    assert aggregate_clip_status({"uploaded", "ready"}) == ClipStatus.UPLOADED


def test_partial():
    assert aggregate_clip_status({"ready", "failed"}) == ClipStatus.PARTIAL


def test_single_unexpected():
    assert aggregate_clip_status({"weird"}) == "weird"
