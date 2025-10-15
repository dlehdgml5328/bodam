"""Selenium crawler service

Handles web page crawling using Selenium WebDriver.
Supports wait conditions and retry logic.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

from src.models.selenium_crawl_job import SeleniumCrawlJob, JobStatus
from src.services.crawler.webdriver_pool import driver_pool

logger = logging.getLogger(__name__)


class WaitConditionType:
    """Wait condition types"""
    ELEMENT_PRESENT = "element_present"
    ELEMENT_VISIBLE = "element_visible"
    PAGE_LOADED = "page_loaded"
    CUSTOM_SCRIPT = "custom_script"


class SeleniumCrawler:
    """
    Selenium web crawler

    Handles crawling web pages with JavaScript rendering support.
    Uses WebDriver pool for efficient resource management.
    """

    def __init__(self):
        self.driver_pool = driver_pool

    def crawl(self, job: SeleniumCrawlJob) -> Dict[str, Any]:
        """
        Crawl a web page based on job configuration

        Args:
            job: SeleniumCrawlJob instance with URL and wait conditions

        Returns:
            dict: {
                "html": rendered HTML,
                "page_source": raw page source,
                "url": final URL (after redirects),
                "title": page title,
                "screenshot": screenshot data (if captured)
            }

        Raises:
            TimeoutException: If wait condition times out
            WebDriverException: If browser operation fails
        """
        driver = None

        try:
            # Acquire WebDriver from pool
            driver = self.driver_pool.acquire(timeout=30)

            logger.info(f"Crawling URL: {job.url}")
            start_time = time.time()

            # Navigate to URL
            driver.get(job.url)

            # Apply wait conditions
            if job.wait_conditions:
                self._apply_wait_conditions(driver, job.wait_conditions)

            # Get page data
            result = {
                "html": driver.page_source,
                "url": driver.current_url,
                "title": driver.title,
                "cookies": driver.get_cookies(),
            }

            elapsed = time.time() - start_time
            logger.info(f"Successfully crawled {job.url} in {elapsed:.2f}s")

            return result

        except TimeoutException as e:
            logger.error(f"Timeout crawling {job.url}: {e}")
            raise

        except NoSuchElementException as e:
            logger.error(f"Element not found on {job.url}: {e}")
            raise

        except WebDriverException as e:
            logger.error(f"WebDriver error crawling {job.url}: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error crawling {job.url}: {e}")
            raise

        finally:
            # Release WebDriver back to pool
            if driver:
                self.driver_pool.release(driver)

    def _apply_wait_conditions(self, driver: webdriver.Chrome, wait_conditions: Dict[str, Any]):
        """
        Apply wait conditions before extracting content

        Args:
            driver: WebDriver instance
            wait_conditions: Wait condition configuration

        Raises:
            TimeoutException: If wait condition not met within timeout
        """
        condition_type = wait_conditions.get("type")
        timeout_seconds = wait_conditions.get("timeout_seconds", 30)

        logger.debug(f"Applying wait condition: {condition_type} (timeout={timeout_seconds}s)")

        wait = WebDriverWait(driver, timeout_seconds)

        if condition_type == WaitConditionType.ELEMENT_PRESENT:
            selector = wait_conditions.get("selector")
            if not selector:
                raise ValueError("selector required for element_present wait condition")

            # Determine selector type (CSS or XPath)
            by = By.CSS_SELECTOR if not selector.startswith("//") else By.XPATH

            wait.until(EC.presence_of_element_located((by, selector)))
            logger.debug(f"Element present: {selector}")

        elif condition_type == WaitConditionType.ELEMENT_VISIBLE:
            selector = wait_conditions.get("selector")
            if not selector:
                raise ValueError("selector required for element_visible wait condition")

            by = By.CSS_SELECTOR if not selector.startswith("//") else By.XPATH

            wait.until(EC.visibility_of_element_located((by, selector)))
            logger.debug(f"Element visible: {selector}")

        elif condition_type == WaitConditionType.PAGE_LOADED:
            # Wait for document.readyState to be 'complete'
            wait.until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            logger.debug("Page loaded (document.readyState == complete)")

            # Additional wait for network idle (if needed)
            time.sleep(1)  # Wait 1 second for pending requests

        elif condition_type == WaitConditionType.CUSTOM_SCRIPT:
            script = wait_conditions.get("script")
            if not script:
                raise ValueError("script required for custom_script wait condition")

            # Execute custom JavaScript and wait for truthy result
            wait.until(lambda d: d.execute_script(script))
            logger.debug(f"Custom script condition met: {script[:50]}...")

        else:
            logger.warning(f"Unknown wait condition type: {condition_type}")

    def take_screenshot(self, driver: webdriver.Chrome, file_path: Optional[str] = None) -> Optional[bytes]:
        """
        Take screenshot of current page

        Args:
            driver: WebDriver instance
            file_path: Optional file path to save screenshot

        Returns:
            Screenshot as bytes (PNG format)
        """
        try:
            if file_path:
                driver.save_screenshot(file_path)
                logger.debug(f"Screenshot saved to {file_path}")
                return None
            else:
                screenshot_bytes = driver.get_screenshot_as_png()
                logger.debug(f"Screenshot captured ({len(screenshot_bytes)} bytes)")
                return screenshot_bytes

        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None

    def extract_element_text(self, driver: webdriver.Chrome, selector: str) -> Optional[str]:
        """
        Extract text from element

        Args:
            driver: WebDriver instance
            selector: CSS selector or XPath

        Returns:
            Element text content or None if not found
        """
        try:
            by = By.CSS_SELECTOR if not selector.startswith("//") else By.XPATH
            element = driver.find_element(by, selector)
            return element.text

        except NoSuchElementException:
            logger.warning(f"Element not found: {selector}")
            return None
