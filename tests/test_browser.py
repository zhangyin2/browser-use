import asyncio
import logging
import pytest
import requests
import subprocess
from browser_use.browser.browser import (
    Browser,
    BrowserConfig,
    async_playwright,
)
from browser_use.browser.context import (
    BrowserContext,
    BrowserContextConfig,
)


class DummyChromium:

    async def connect_over_cdp(self, url):
        return None


class DummyPlaywright:
    chromium = DummyChromium()


@pytest.mark.asyncio
async def test_setup_cdp_without_url():
    """
    Test that _setup_cdp raises a ValueError when no CDP URL is provided in BrowserConfig.
    """
    config = BrowserConfig(cdp_url=None)
    browser = Browser(config=config)
    with pytest.raises(ValueError, match="CDP URL is required"):
        await browser._setup_cdp(DummyPlaywright())


class DummyChromiumWithLaunch:

    async def launch(self, headless, args, proxy):
        """
        Dummy launch method that validates passed parameters and returns a dummy browser.
        """
        assert headless == False
        assert "--no-sandbox" in args
        return "dummy_browser"


class DummyPlaywrightStandard:
    chromium = DummyChromiumWithLaunch()


@pytest.mark.asyncio
async def test_setup_standard_browser():
    """
    Test that _setup_browser returns a standard browser instance when no remote URL or chrome instance path is provided.
    """
    config = BrowserConfig()
    browser_instance = Browser(config=config)
    result = await browser_instance._setup_browser(DummyPlaywrightStandard())
    assert result == "dummy_browser"


class DummyChromiumWSS:

    async def connect(self, url, timeout=None):
        """
        Dummy connect method for WebSocket that validates the URL and returns a dummy browser.
        """
        assert url == "wss://dummy"
        return "dummy_wss_browser"


class DummyPlaywrightWSS:
    chromium = DummyChromiumWSS()


@pytest.mark.asyncio
async def test_setup_wss_browser():
    """
    Test that _setup_browser returns a browser instance via WSS connection when wss_url is provided.
    """
    config = BrowserConfig(wss_url="wss://dummy")
    browser_instance = Browser(config=config)
    result = await browser_instance._setup_browser(DummyPlaywrightWSS())
    assert result == "dummy_wss_browser"


class DummyChromiumInstance:

    async def connect_over_cdp(self, endpoint_url, timeout):
        assert endpoint_url == "http://localhost:9222"
        assert timeout == 20000
        return "dummy_chrome_instance_browser"


class DummyPlaywrightInstance:
    chromium = DummyChromiumInstance()


@pytest.mark.asyncio
async def test_setup_browser_with_instance(monkeypatch):
    """
    Test that _setup_browser_with_instance starts a new Chrome instance by simulating connection failures
    and then a successful connection. This verifies that the for-loop waiting for a newly started Chrome instance works.
    """
    fake_get_calls = []

    def fake_get(url, timeout):
        if len(fake_get_calls) < 3:
            fake_get_calls.append(1)
            raise requests.ConnectionError("Simulated connection error")
        else:

            class DummyResponse:
                status_code = 200

            return DummyResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(subprocess, "Popen", lambda args, stdout, stderr: None)
    config = BrowserConfig(chrome_instance_path="dummy_chrome_instance_path")
    browser_instance = Browser(config=config)
    result = await browser_instance._setup_browser_with_instance(
        DummyPlaywrightInstance()
    )
    assert result == "dummy_chrome_instance_browser"


class DummyFailingBrowser:

    async def close(self):
        raise Exception("Simulated close error")


class DummyFailingPlaywright:

    async def stop(self):
        raise Exception("Simulated stop error")


@pytest.mark.asyncio
async def test_close_cleans_up_resources():
    """
    Test that calling close() cleans up the browser instance by setting playwright_browser and playwright to None,
    even if the underlying close() and stop() methods throw exceptions.
    """
    config = BrowserConfig()
    browser_instance = Browser(config=config)
    browser_instance.playwright_browser = DummyFailingBrowser()
    browser_instance.playwright = DummyFailingPlaywright()
    await browser_instance.close()
    assert browser_instance.playwright_browser is None
    assert browser_instance.playwright is None


class DummyAsyncPlaywrightWrapper:
    """Dummy wrapper to simulate async_playwright() call.
    Its start() method returns a DummyPlaywrightStandard instance."""

    async def start(self):
        return DummyPlaywrightStandard()


@pytest.mark.asyncio
async def test_get_playwright_browser_initializes_browser(monkeypatch):
    """
    Test that get_playwright_browser initializes the browser correctly.
    The test monkeypatches async_playwright to use a dummy implementation so that the
    first call to get_playwright_browser initializes the browser via _init (returning "dummy_browser")
    and subsequent calls do not reinitialize the browser.
    """
    monkeypatch.setattr(
        "browser_use.browser.browser.async_playwright",
        lambda: DummyAsyncPlaywrightWrapper(),
    )
    config = BrowserConfig()
    browser_instance = Browser(config=config)
    assert browser_instance.playwright_browser is None
    result = await browser_instance.get_playwright_browser()
    assert result == "dummy_browser"
    assert browser_instance.playwright_browser == "dummy_browser"
    assert browser_instance.playwright is not None
    result2 = await browser_instance.get_playwright_browser()
    assert result2 == "dummy_browser"
    await browser_instance.close()


def test_disable_security_flag():
    """
    Test that the browser's disable_security_args are set correctly based on the configuration flag.

    When disable_security is True, the disable_security_args should contain the expected flags.
    When disable_security is False, disable_security_args should be an empty list.
    """
    config_true = BrowserConfig(disable_security=True)
    browser_true = Browser(config=config_true)
    expected_args = [
        "--disable-web-security",
        "--disable-site-isolation-trials",
        "--disable-features=IsolateOrigins,site-per-process",
    ]
    assert browser_true.disable_security_args == expected_args
    config_false = BrowserConfig(disable_security=False)
    browser_false = Browser(config=config_false)
    assert browser_false.disable_security_args == []


class DummyChromiumForCDP:

    async def connect_over_cdp(self, url):
        """
        Dummy connect_over_cdp method that validates the URL and returns a dummy browser.
        """
        assert url == "http://dummy-cdp", "Unexpected CDP URL"
        return "dummy_cdp_browser"


class DummyPlaywrightForCDP:
    chromium = DummyChromiumForCDP()


@pytest.mark.asyncio
async def test_setup_cdp_browser():
    """
    Test that _setup_cdp correctly connects to a remote browser via CDP when a valid URL is provided.
    This test creates a dummy Playwright instance with a dummy Chromium implementation.
    """
    config = BrowserConfig(cdp_url="http://dummy-cdp")
    browser_instance = Browser(config=config)
    result = await browser_instance._setup_cdp(DummyPlaywrightForCDP())
    assert result == "dummy_cdp_browser"


@pytest.mark.asyncio
async def test_new_context_creates_instance():
    """
    Test that new_context method of Browser returns a valid BrowserContext instance
    with the correct configuration and associated browser.
    """
    custom_context_config = BrowserContextConfig()
    config = BrowserConfig()
    browser_instance = Browser(config=config)
    context = await browser_instance.new_context(custom_context_config)
    assert isinstance(context, BrowserContext)
    assert context.config == custom_context_config
    assert context.browser == browser_instance


@pytest.mark.asyncio
async def test_setup_browser_priority_cdp_over_wss():
    """
    Test that _setup_browser prioritizes a CDP connection over a WSS connection
    when both URLs are provided in the configuration.
    """

    class DummyChromiumPriority:

        async def connect_over_cdp(self, url):
            assert (
                url == "http://dummy-cdp"
            ), f"Expected CDP URL 'http://dummy-cdp', got {url}"
            return "dummy_cdp_browser"

        async def connect(self, url, timeout=None):
            raise Exception(
                "WSS connect method should not be called when CDP URL is available"
            )

    class DummyPlaywrightPriority:
        chromium = DummyChromiumPriority()

    config = BrowserConfig(cdp_url="http://dummy-cdp", wss_url="wss://dummy")
    browser_instance = Browser(config=config)
    result = await browser_instance._setup_browser(DummyPlaywrightPriority())
    assert result == "dummy_cdp_browser"
