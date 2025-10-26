"""NFDS (국가화재정보시스템) 크롤러

소방청 국가화재정보시스템에서 실시간 화재출동현황 데이터를 크롤링
Selenium을 사용하여 JavaScript 렌더링된 데이터 수집
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.services.crawler.webdriver_pool import driver_pool

logger = logging.getLogger(__name__)

NFDS_URL = "https://nfds.go.kr/dashboard/monitor.do"


class NFDSCrawler:
    """
    NFDS 국가화재정보시스템 크롤러

    실시간 화재출동현황을 크롤링하여 구조화된 데이터로 반환
    """

    def __init__(self):
        self.driver_pool = driver_pool
        self.url = NFDS_URL

    def crawl(self) -> List[Dict[str, Any]]:
        """
        NFDS에서 화재출동현황 크롤링

        Returns:
            List[Dict]: 화재출동 데이터 리스트
            [
                {
                    "id": "20251009007",
                    "fireName": "평산소방서",
                    "occurrenceDate": "2025-10-09",
                    "occurrenceTime": "09:10",
                    "deaths": 0,
                    "injured": 0,
                    "damageAmount": 0,
                    "address": "경기 안산시 단원구 선부동 아파트",
                    "status": "화재접수"
                },
                ...
            ]

        Raises:
            TimeoutException: 페이지 로딩 시간 초과
            WebDriverException: 브라우저 오류
        """
        driver = None

        try:
            # WebDriver 획득
            driver = self.driver_pool.acquire(timeout=30)
            logger.info(f"[NFDS Crawler] Starting crawl from {self.url}")

            # 페이지 로드
            driver.get(self.url)

            # 테이블이 로드될 때까지 대기 (최대 30초)
            wait = WebDriverWait(driver, 30)
            wait.until(
                EC.presence_of_element_located((By.ID, "grdViewer"))
            )

            # AJAX 데이터 로딩 대기 (추가 2초)
            time.sleep(2)

            logger.info("[NFDS Crawler] Page loaded, parsing table data")

            # 테이블 데이터 파싱
            incidents = self._parse_table(driver)

            logger.info(f"[NFDS Crawler] Successfully crawled {len(incidents)} incidents")

            return incidents

        except TimeoutException as e:
            logger.error(f"[NFDS Crawler] Timeout loading page: {e}")
            raise

        except WebDriverException as e:
            logger.error(f"[NFDS Crawler] WebDriver error: {e}")
            raise

        except Exception as e:
            logger.error(f"[NFDS Crawler] Unexpected error: {e}", exc_info=True)
            raise

        finally:
            # WebDriver 반환
            if driver:
                self.driver_pool.release(driver)

    def _parse_table(self, driver: webdriver.Chrome) -> List[Dict[str, Any]]:
        """
        NFDS 테이블 데이터 파싱

        Args:
            driver: WebDriver 인스턴스

        Returns:
            List[Dict]: 파싱된 화재출동 데이터
        """
        incidents = []

        try:
            # 테이블 찾기
            table = driver.find_element(By.ID, "grdViewer")

            # tbody 내의 모든 행 찾기
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")

            logger.info(f"[NFDS Parser] Found {len(rows)} rows in table")

            for idx, row in enumerate(rows):
                try:
                    incident = self._parse_row(row, idx)
                    if incident:
                        incidents.append(incident)
                except Exception as e:
                    logger.warning(f"[NFDS Parser] Failed to parse row {idx}: {e}")
                    continue

        except NoSuchElementException as e:
            logger.error(f"[NFDS Parser] Table not found: {e}")
            raise

        return incidents

    def _parse_row(self, row, row_index: int) -> Optional[Dict[str, Any]]:
        """
        테이블 행 파싱

        NFDS 테이블 구조:
        - 컬럼 0: 소방서 (fireName)
        - 컬럼 1: 일시 (occurrenceTime)
        - 컬럼 2: 사망 (deaths)
        - 컬럼 3: 부상 (injured)
        - 컬럼 4: 재산피해(천원) (damageAmount)
        - 컬럼 5: 주소 (address)
        - 컬럼 6: 진행상태 (status)

        Args:
            row: tr 요소
            row_index: 행 인덱스

        Returns:
            Dict: 파싱된 데이터 또는 None
        """
        try:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) < 7:
                logger.warning(f"[NFDS Parser] Row {row_index} has insufficient cells: {len(cells)}")
                return None

            # 각 셀에서 텍스트 추출
            fire_name = cells[0].text.strip()
            occurrence_time_raw = cells[1].text.strip()  # "09:10" 형식
            deaths_raw = cells[2].text.strip()
            injured_raw = cells[3].text.strip()
            damage_raw = cells[4].text.strip()
            address = cells[5].text.strip()
            status = cells[6].text.strip()

            # 데이터 검증 (빈 행 스킵)
            if not fire_name or fire_name == "-":
                return None

            # 날짜/시간 파싱
            # NFDS는 "09:10" 형식으로만 제공하므로 오늘 날짜 사용
            today = datetime.now()
            occurrence_date = today.strftime("%Y-%m-%d")
            occurrence_time = occurrence_time_raw if occurrence_time_raw != "-" else "00:00"

            # 사망자 수 파싱
            deaths = self._parse_number(deaths_raw)

            # 부상자 수 파싱
            injured = self._parse_number(injured_raw)

            # 재산피해액 파싱 (천원 단위 → 원 단위)
            damage_amount = self._parse_number(damage_raw)
            if damage_amount > 0:
                damage_amount *= 1000  # 천원 → 원

            # 고유 ID 생성 (소방서명 + 일시 해시)
            # 실제로는 NFDS에 고유 ID가 있을 수 있지만, 보이지 않으므로 생성
            incident_id = self._generate_incident_id(fire_name, occurrence_date, occurrence_time)

            # NFDS 상태를 코드로 매핑
            status_code = self._map_status_to_code(status)

            incident = {
                "id": incident_id,
                "fireName": fire_name,
                "occurrenceDate": occurrence_date,
                "occurrenceTime": occurrence_time,
                "deaths": deaths,
                "injured": injured,
                "damageAmount": damage_amount,
                "address": address,
                "status": status_code,  # A/B/C/D 코드로 변환
                "axisX": 0.0,  # NFDS 테이블에는 좌표 정보 없음
                "axisY": 0.0,
                "progress": status,  # 원래 한글 상태
                "casualties": deaths + injured,  # 총 사상자 수
                "crawledAt": datetime.now().isoformat()
            }

            logger.debug(f"[NFDS Parser] Parsed incident: {incident_id} - {fire_name}")

            return incident

        except Exception as e:
            logger.error(f"[NFDS Parser] Error parsing row {row_index}: {e}", exc_info=True)
            return None

    def _parse_number(self, text: str) -> int:
        """
        숫자 텍스트 파싱

        Args:
            text: "0", "2", "-" 등

        Returns:
            int: 파싱된 숫자 (파싱 실패 시 0)
        """
        if not text or text == "-":
            return 0

        try:
            # 숫자만 추출
            numbers = re.findall(r"\d+", text)
            if numbers:
                return int(numbers[0])
            return 0
        except Exception:
            return 0

    def _map_status_to_code(self, status_text: str) -> str:
        """
        NFDS 상태 텍스트를 코드로 매핑

        Args:
            status_text: NFDS 상태 텍스트 (예: "화재접수", "출동중", "진압중", "귀소")

        Returns:
            str: 상태 코드 (A: 출동중, B: 진압중, C: 진압완료, D: 귀소)
        """
        status_map = {
            "화재접수": "A",  # 출동중
            "출동중": "A",
            "현장도착": "B",  # 진압중
            "진압중": "B",
            "완진": "C",      # 진압완료
            "진압완료": "C",
            "귀소": "D",      # 귀소
            "조치완료": "D",
        }

        # 기본값은 D (귀소/완료)
        return status_map.get(status_text, "D")

    def _generate_incident_id(self, fire_name: str, date: str, time: str) -> str:
        """
        화재 사고 고유 ID 생성

        Args:
            fire_name: 소방서명
            date: 발생일자 (YYYY-MM-DD)
            time: 발생시간 (HH:MM)

        Returns:
            str: 생성된 ID (예: "20251017_0910_평산소방서")
        """
        # 날짜 포맷: YYYYMMDD
        date_compact = date.replace("-", "")
        # 시간 포맷: HHMM
        time_compact = time.replace(":", "")

        # ID 생성: YYYYMMDD_HHMM_소방서명
        incident_id = f"{date_compact}_{time_compact}_{fire_name}"

        return incident_id


# 싱글톤 인스턴스
nfds_crawler = NFDSCrawler()
