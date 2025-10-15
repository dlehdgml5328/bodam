"""WebDriver Pool 단위 테스트"""

import pytest
from unittest.mock import Mock, patch
from queue import Queue, Empty
from selenium import webdriver

from src.services.crawler.webdriver_pool import WebDriverPool


class TestWebDriverPool:
    """WebDriver 풀 테스트 케이스"""

    def test_pool_initialization(self):
        """풀이 올바른 크기로 초기화되는지 확인"""
        pool = WebDriverPool(max_size=5)
        assert pool.max_size == 5
        assert pool.pool.maxsize == 5

    @patch('src.services.crawler.webdriver_pool.webdriver.Chrome')
    def test_acquire_creates_driver_when_pool_empty(self, mock_chrome):
        """풀이 비어있을 때 새 드라이버를 생성하는지 확인"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        pool = WebDriverPool(max_size=3)
        driver = pool.acquire(timeout=1)
        
        assert driver == mock_driver
        mock_chrome.assert_called_once()

    @patch('src.services.crawler.webdriver_pool.webdriver.Chrome')
    def test_acquire_reuses_driver_from_pool(self, mock_chrome):
        """풀에 드라이버가 있을 때 재사용하는지 확인"""
        mock_driver = Mock()
        
        pool = WebDriverPool(max_size=3)
        pool.pool.put(mock_driver)
        
        driver = pool.acquire(timeout=1)
        
        assert driver == mock_driver
        # Chrome 생성자가 호출되지 않아야 함
        mock_chrome.assert_not_called()

    @patch('src.services.crawler.webdriver_pool.webdriver.Chrome')
    def test_acquire_timeout(self, mock_chrome):
        """타임아웃 시 예외를 발생시키는지 확인"""
        pool = WebDriverPool(max_size=1)
        
        # 풀을 가득 채움
        with patch.object(pool.pool, 'get', side_effect=Empty):
            mock_chrome.side_effect = Exception("Driver creation failed")
            
            with pytest.raises(Exception):
                pool.acquire(timeout=0.1)

    @patch('src.services.crawler.webdriver_pool.webdriver.Chrome')
    def test_release_cleans_driver_state(self, mock_chrome):
        """드라이버 릴리스 시 상태를 초기화하는지 확인"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        pool = WebDriverPool(max_size=3)
        driver = pool.acquire()
        pool.release(driver)
        
        # 쿠키 삭제, 로컬 스토리지 클리어, 빈 페이지로 이동 확인
        mock_driver.delete_all_cookies.assert_called_once()
        mock_driver.execute_script.assert_called_once_with("window.localStorage.clear();")
        mock_driver.get.assert_called_once_with("about:blank")

    @patch('src.services.crawler.webdriver_pool.webdriver.Chrome')
    def test_release_returns_driver_to_pool(self, mock_chrome):
        """드라이버가 풀로 반환되는지 확인"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        pool = WebDriverPool(max_size=3)
        driver = pool.acquire()
        
        assert pool.pool.qsize() == 0
        pool.release(driver)
        assert pool.pool.qsize() == 1

    @patch('src.services.crawler.webdriver_pool.webdriver.Chrome')
    def test_multiple_acquire_release_cycles(self, mock_chrome):
        """여러 번의 획득/반환 사이클이 올바르게 동작하는지 확인"""
        mock_drivers = [Mock() for _ in range(3)]
        mock_chrome.side_effect = mock_drivers
        
        pool = WebDriverPool(max_size=3)
        
        # 3개 드라이버 획득
        d1 = pool.acquire()
        d2 = pool.acquire()
        d3 = pool.acquire()
        
        # 2개 반환
        pool.release(d1)
        pool.release(d2)
        
        assert pool.pool.qsize() == 2
        
        # 다시 획득 (재사용되어야 함)
        d4 = pool.acquire()
        assert d4 in [d1, d2]

    @patch('src.services.crawler.webdriver_pool.webdriver.Chrome')
    def test_driver_options_headless(self, mock_chrome):
        """헤드리스 옵션이 설정되는지 확인"""
        pool = WebDriverPool(max_size=1)
        driver = pool.acquire()
        
        # Chrome 호출 시 options 인자 확인
        call_kwargs = mock_chrome.call_args[1]
        assert 'options' in call_kwargs
        options = call_kwargs['options']
        assert '--headless' in options.arguments

    @patch('src.services.crawler.webdriver_pool.webdriver.Chrome')
    def test_concurrent_access(self, mock_chrome):
        """동시 접근 시 스레드 안전성 확인"""
        import threading
        
        mock_drivers = [Mock() for _ in range(10)]
        mock_chrome.side_effect = mock_drivers
        
        pool = WebDriverPool(max_size=10)
        acquired_drivers = []
        errors = []
        
        def acquire_and_release():
            try:
                driver = pool.acquire(timeout=5)
                acquired_drivers.append(driver)
                pool.release(driver)
            except Exception as e:
                errors.append(e)
        
        # 10개 스레드 동시 실행
        threads = [threading.Thread(target=acquire_and_release) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert len(acquired_drivers) == 10
