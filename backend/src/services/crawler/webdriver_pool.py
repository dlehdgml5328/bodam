"""WebDriver connection pool

Manages a pool of Selenium WebDriver instances for reuse.
Reduces browser startup overhead (2-3 seconds per instance).
"""

from __future__ import annotations

import atexit
import logging
from queue import Queue, Empty
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class WebDriverPool:
    """
    WebDriver connection pool

    Maintains a pool of Chrome WebDriver instances that can be reused
    across multiple crawl jobs. Instances are reset between jobs.
    """

    def __init__(self, max_size: int = 10):
        """
        Initialize WebDriver pool

        Args:
            max_size: Maximum number of WebDriver instances in pool
        """
        self.max_size = max_size
        self.pool: Queue = Queue(maxsize=max_size)
        self._initialized = False

        logger.info(f"Initializing WebDriver pool with max_size={max_size}")

    def _create_driver(self) -> webdriver.Chrome:
        """Create a new Chrome WebDriver instance"""
        options = Options()
        options.add_argument("--headless")  # Run without GUI
        options.add_argument("--no-sandbox")  # Required for Docker
        options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
        options.add_argument("--disable-gpu")  # Applicable to Windows
        options.add_argument("--window-size=1920,1080")  # Set viewport size
        options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection

        # Use webdriver-manager to automatically download matching ChromeDriver
        service = Service(ChromeDriverManager().install())

        driver = webdriver.Chrome(service=service, options=options)

        # Set timeouts
        driver.set_page_load_timeout(30)  # Page load timeout: 30s
        driver.set_script_timeout(10)  # JavaScript execution timeout: 10s

        logger.info(f"Created new WebDriver instance: {driver.session_id}")
        return driver

    def _initialize_pool(self):
        """Initialize pool with WebDriver instances"""
        if self._initialized:
            return

        logger.info(f"Initializing {self.max_size} WebDriver instances...")

        for i in range(self.max_size):
            try:
                driver = self._create_driver()
                self.pool.put(driver)
                logger.info(f"Added driver {i+1}/{self.max_size} to pool")
            except Exception as e:
                logger.error(f"Failed to create driver {i+1}: {e}")
                # Continue with fewer drivers

        self._initialized = True
        logger.info(f"Pool initialized with {self.pool.qsize()} drivers")

    def acquire(self, timeout: Optional[float] = 30) -> webdriver.Chrome:
        """
        Acquire a WebDriver from the pool

        Args:
            timeout: Maximum time to wait for available driver (seconds)

        Returns:
            Chrome WebDriver instance

        Raises:
            Empty: If no driver available within timeout
        """
        if not self._initialized:
            self._initialize_pool()

        try:
            driver = self.pool.get(timeout=timeout)
            logger.debug(f"Acquired driver from pool: {driver.session_id}")
            return driver
        except Empty:
            logger.error(f"No WebDriver available within {timeout}s (pool exhausted)")
            raise RuntimeError(f"WebDriver pool exhausted (max_size={self.max_size})")

    def release(self, driver: webdriver.Chrome):
        """
        Release a WebDriver back to the pool

        Resets driver state (cookies, storage) before returning to pool.

        Args:
            driver: WebDriver instance to release
        """
        try:
            # Reset driver state
            driver.delete_all_cookies()

            # Clear local/session storage
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")

            # Navigate to blank page to free memory
            driver.get("about:blank")

            self.pool.put(driver)
            logger.debug(f"Released driver to pool: {driver.session_id}")

        except Exception as e:
            logger.error(f"Error releasing driver: {e}")
            # Don't return broken driver to pool
            try:
                driver.quit()
            except:
                pass

    def cleanup(self):
        """Cleanup all WebDriver instances in pool"""
        logger.info("Cleaning up WebDriver pool...")

        while not self.pool.empty():
            try:
                driver = self.pool.get_nowait()
                driver.quit()
                logger.debug(f"Closed driver: {driver.session_id}")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")

        logger.info("WebDriver pool cleanup complete")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()


# Global driver pool instance
driver_pool = WebDriverPool(max_size=10)

# Register cleanup on exit
atexit.register(driver_pool.cleanup)
