"""Tests for the background GitHub update monitor."""

from unittest.mock import MagicMock, patch

from vocalinux.utils.update_checker import ReleaseInfo
from vocalinux.utils.update_monitor import UpdateMonitor


def _release(tag: str = "v0.99.0") -> ReleaseInfo:
    return ReleaseInfo(
        tag_name=tag,
        version=tag.lstrip("v"),
        name=tag,
        html_url=f"https://github.com/jatinkrmalik/vocalinux/releases/tag/{tag}",
        body="Notes",
        published_at="2026-08-06T00:00:00Z",
        prerelease=False,
        channel="stable",
    )


class TestUpdateMonitor:
    def test_start_schedules_without_immediate_check(self):
        on_result = MagicMock()
        monitor = UpdateMonitor(
            get_channel=lambda: "stable",
            on_result=on_result,
            get_current_version=lambda: "0.1.0",
            startup_delay_seconds=45,
            check_interval_seconds=3600,
            use_glib=False,
        )
        monitor.start()
        assert monitor.active
        assert monitor.tick() is False  # not due yet
        on_result.assert_not_called()
        monitor.stop()
        assert not monitor.active

    def test_check_now_reports_available_update(self):
        on_result = MagicMock()
        release = _release("v0.99.0")
        monitor = UpdateMonitor(
            get_channel=lambda: "stable",
            on_result=on_result,
            get_current_version=lambda: "0.15.0",
            use_glib=False,
        )
        monitor.start()

        with patch(
            "vocalinux.utils.update_monitor.fetch_latest_release",
            return_value=release,
        ):
            # Run worker synchronously by calling it directly.
            monitor._check_in_progress = False
            monitor._worker("stable", "0.15.0", monitor._generation)

        on_result.assert_called_once_with(True, release)
        assert monitor.last_available is True
        assert monitor.last_release is release
        monitor.stop()

    def test_check_now_reports_up_to_date(self):
        on_result = MagicMock()
        release = _release("v0.15.0")
        monitor = UpdateMonitor(
            get_channel=lambda: "stable",
            on_result=on_result,
            get_current_version=lambda: "0.15.0",
            use_glib=False,
        )
        monitor.start()

        with patch(
            "vocalinux.utils.update_monitor.fetch_latest_release",
            return_value=release,
        ):
            monitor._worker("stable", "0.15.0", monitor._generation)

        on_result.assert_called_once_with(False, None)
        assert monitor.last_available is False
        monitor.stop()

    def test_failed_fetch_keeps_prior_available_state(self):
        on_result = MagicMock()
        release = _release("v0.99.0")
        monitor = UpdateMonitor(
            get_channel=lambda: "stable",
            on_result=on_result,
            get_current_version=lambda: "0.15.0",
            use_glib=False,
        )
        monitor.start()

        with patch(
            "vocalinux.utils.update_monitor.fetch_latest_release",
            return_value=release,
        ):
            monitor._worker("stable", "0.15.0", monitor._generation)
        on_result.reset_mock()

        with patch(
            "vocalinux.utils.update_monitor.fetch_latest_release",
            return_value=None,
        ):
            monitor._worker("stable", "0.15.0", monitor._generation)

        on_result.assert_not_called()
        assert monitor.last_available is True
        assert monitor.last_release is release
        monitor.stop()

    def test_stale_generation_is_ignored(self):
        on_result = MagicMock()
        monitor = UpdateMonitor(
            get_channel=lambda: "stable",
            on_result=on_result,
            get_current_version=lambda: "0.15.0",
            use_glib=False,
        )
        monitor.start()
        stale = monitor._generation
        monitor._generation += 1

        with patch(
            "vocalinux.utils.update_monitor.fetch_latest_release",
            return_value=_release(),
        ):
            monitor._worker("stable", "0.15.0", stale)

        on_result.assert_not_called()
        monitor.stop()

    def test_tick_fires_when_due(self):
        on_result = MagicMock()
        monitor = UpdateMonitor(
            get_channel=lambda: "stable",
            on_result=on_result,
            get_current_version=lambda: "0.15.0",
            startup_delay_seconds=0,
            check_interval_seconds=60,
            use_glib=False,
        )
        monitor.start()
        # Force due immediately.
        monitor._next_due_at = 0
        with patch.object(monitor, "_run_check") as run_check:
            assert monitor.tick() is True
            run_check.assert_called_once()
        monitor.stop()
