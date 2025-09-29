'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';

export default function RegionsPage() {
  const router = useRouter();
  const [selectedRegion, setSelectedRegion] = useState('전국');
  const [selectedStatus, setSelectedStatus] = useState('전체');
  const [showRegionDetail, setShowRegionDetail] = useState(false);
  const [selectedRegionData, setSelectedRegionData] = useState<any>(null);

  // 복수 기부 관련 상태 추가
  const [showMultipleDonationModal, setShowMultipleDonationModal] = useState(false);
  const [donationType, setDonationType] = useState<'split' | 'each'>('split');
  const [selectedFireStations, setSelectedFireStations] = useState<string[]>([]);
  const [tempSelectedStations, setTempSelectedStations] = useState<string[]>([]);
  const [searchStation, setSearchStation] = useState('');
  const [showRegionModal, setShowRegionModal] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [selectAllStations, setSelectAllStations] = useState(false);

  const regions = ['전국', '서울특별시', '부산광역시', '대구광역시', '인천광역시', '광주광역시', '대전광역시', '울산광역시', '세종특별자치시', '경기도', '강원특별자치도', '충청북도', '충청남도', '전라북도', '전라남도', '경상북도', '경상남도', '제주특별자치도'];
  const statusTypes = ['전체', '화재접수', '출동중', '진압중'];

  const totalStats = {
    totalStations: 1847,
    fireReportStations: 1634,
    onDutyStations: 156,
    suppressingStations: 57
  };

  const monthlyStats = [
    { month: '1월', incidents: 12584 },
    { month: '2월', incidents: 11293 },
    { month: '3월', incidents: 13456 },
    { month: '총 합계', incidents: 37333 }
  ];

  const emergencyIncidents = [
    {
      region: '서울',
      station: '서울중부소방서',
      location: '서울시 중구 명동',
      incident: '아파트 화재',
      status: '진압중',
      time: '3분 전',
      vehicles: 5,
      personnel: 23
    },
    {
      region: '부산',
      station: '부산해운대소방서',
      location: '부산시 해운대구 우동',
      incident: '상가건물 화재',
      status: '출동중',
      time: '8분 전',
      vehicles: 7,
      personnel: 31
    },
    {
      region: '대구',
      station: '대구남부소방서',
      location: '대구시 남구 대명동',
      incident: '교통사고 구조',
      status: '현장도착',
      time: '12분 전',
      vehicles: 3,
      personnel: 12
    },
    {
      region: '인천',
      station: '인천연수소방서',
      location: '인천시 연수구 송도동',
      incident: '엘리베이터 갇힘',
      status: '구조완료',
      time: '25분 전',
      vehicles: 2,
      personnel: 8
    }
  ];

  // 시별로 세분화된 지역별 소방서 데이터 - 실제 숫자에 맞게 조정
  const fireStationsByRegion = [
    { region: '서울특별시', total: 150, fireReport: 140, onDuty: 7, suppressing: 3 },
    { region: '부산광역시', total: 95, fireReport: 88, onDuty: 4, suppressing: 3 },
    { region: '대구광역시', total: 72, fireReport: 67, onDuty: 3, suppressing: 2 },
    { region: '인천광역시', total: 85, fireReport: 79, onDuty: 4, suppressing: 2 },
    { region: '광주광역시', total: 48, fireReport: 44, onDuty: 2, suppressing: 2 },
    { region: '대전광역시', total: 42, fireReport: 39, onDuty: 2, suppressing: 1 },
    { region: '울산광역시', total: 38, fireReport: 35, onDuty: 2, suppressing: 1 },
    { region: '세종특별자치시', total: 15, fireReport: 14, onDuty: 1, suppressing: 0 },
    { region: '경기도', total: 245, fireReport: 228, onDuty: 12, suppressing: 5 },
    { region: '강원특별자치도', total: 98, fireReport: 90, onDuty: 5, suppressing: 3 },
    { region: '충청북도', total: 75, fireReport: 69, onDuty: 4, suppressing: 2 },
    { region: '충청남도', total: 88, fireReport: 81, onDuty: 4, suppressing: 3 },
    { region: '전라북도', total: 82, fireReport: 75, onDuty: 4, suppressing: 3 },
    { region: '전라남도', total: 105, fireReport: 96, onDuty: 6, suppressing: 3 },
    { region: '경상북도', total: 135, fireReport: 124, onDuty: 7, suppressing: 4 },
    { region: '경상남도', total: 118, fireReport: 108, onDuty: 6, suppressing: 4 },
    { region: '제주특별자치도', total: 32, fireReport: 29, onDuty: 2, suppressing: 1 }
  ];

  // 전체 소방서 데이터 - 시별로 세분화
  const allFireStations = [
    // 서울특별시 (25개 자치구)
    { id: 1, name: '서울중구소방서', region: '서울특별시', city: '중구' },
    { id: 2, name: '서울종로소방서', region: '서울특별시', city: '종로구' },
    { id: 3, name: '서울용산소방서', region: '서울특별시', city: '용산구' },
    { id: 4, name: '서울성동소방서', region: '서울특별시', city: '성동구' },
    { id: 5, name: '서울광진소방서', region: '서울특별시', city: '광진구' },
    { id: 6, name: '서울동대문소방서', region: '서울특별시', city: '동대문구' },
    { id: 7, name: '서울중랑소방서', region: '서울특별시', city: '중랑구' },
    { id: 8, name: '서울성북소방서', region: '서울특별시', city: '성북구' },
    { id: 9, name: '서울강북소방서', region: '서울특별시', city: '강북구' },
    { id: 10, name: '서울도봉소방서', region: '서울특별시', city: '도봉구' },
    { id: 11, name: '서울노원소방서', region: '서울특별시', city: '노원구' },
    { id: 12, name: '서울은평소방서', region: '서울특별시', city: '은평구' },
    { id: 13, name: '서울서대문소방서', region: '서울특별시', city: '서대문구' },
    { id: 14, name: '서울마포소방서', region: '서울특별시', city: '마포구' },
    { id: 15, name: '서울양천소방서', region: '서울특별시', city: '양천구' },
    { id: 16, name: '서울강서소방서', region: '서울특별시', city: '강서구' },
    { id: 17, name: '서울구로소방서', region: '서울특별시', city: '구로구' },
    { id: 18, name: '서울금천소방서', region: '서울특별시', city: '금천구' },
    { id: 19, name: '서울영등포소방서', region: '서울특별시', city: '영등포구' },
    { id: 20, name: '서울동작소방서', region: '서울특별시', city: '동작구' },
    { id: 21, name: '서울관악소방서', region: '서울특별시', city: '관악구' },
    { id: 22, name: '서울서초소방서', region: '서울특별시', city: '서초구' },
    { id: 23, name: '서울강남소방서', region: '서울특별시', city: '강남구' },
    { id: 24, name: '서울송파소방서', region: '서울특별시', city: '송파구' },
    { id: 25, name: '서울강동소방서', region: '서울특별시', city: '강동구' },
    
    // 부산광역시 (16개 구·군)
    { id: 26, name: '부산중구소방서', region: '부산광역시', city: '중구' },
    { id: 27, name: '부산서구소방서', region: '부산광역시', city: '서구' },
    { id: 28, name: '부산동구소방서', region: '부산광역시', city: '동구' },
    { id: 29, name: '부산영도소방서', region: '부산광역시', city: '영도구' },
    { id: 30, name: '부산부산진소방서', region: '부산광역시', city: '부산진구' },
    { id: 31, name: '부산동래소방서', region: '부산광역시', city: '동래구' },
    { id: 32, name: '부산남구소방서', region: '부산광역시', city: '남구' },
    { id: 33, name: '부산북구소방서', region: '부산광역시', city: '북구' },
    { id: 34, name: '부산해운대소방서', region: '부산광역시', city: '해운대구' },
    { id: 35, name: '부산사하소방서', region: '부산광역시', city: '사하구' },
    { id: 36, name: '부산금정소방서', region: '부산광역시', city: '금정구' },
    { id: 37, name: '부산강서소방서', region: '부산광역시', city: '강서구' },
    { id: 38, name: '부산연제소방서', region: '부산광역시', city: '연제구' },
    { id: 39, name: '부산수영소방서', region: '부산광역시', city: '수영구' },
    { id: 40, name: '부산사상소방서', region: '부산광역시', city: '사상구' },
    { id: 41, name: '부산기장소방서', region: '부산광역시', city: '기장군' },
    
    // 대구광역시 (8개 구·군)
    { id: 42, name: '대구중구소방서', region: '대구광역시', city: '중구' },
    { id: 43, name: '대구동구소방서', region: '대구광역시', city: '동구' },
    { id: 44, name: '대구서구소방서', region: '대구광역시', city: '서구' },
    { id: 45, name: '대구남구소방서', region: '대구광역시', city: '남구' },
    { id: 46, name: '대구북구소방서', region: '대구광역시', city: '북구' },
    { id: 47, name: '대구수성소방서', region: '대구광역시', city: '수성구' },
    { id: 48, name: '대구달서소방서', region: '대구광역시', city: '달서구' },
    { id: 49, name: '대구달성소방서', region: '대구광역시', city: '달성군' },
    
    // 인천광역시 (10개 구·군)
    { id: 50, name: '인천중구소방서', region: '인천광역시', city: '중구' },
    { id: 51, name: '인천동구소방서', region: '인천광역시', city: '동구' },
    { id: 52, name: '인천미추홀소방서', region: '인천광역시', city: '미추홀구' },
    { id: 53, name: '인천연수소방서', region: '인천광역시', city: '연수구' },
    { id: 54, name: '인천남동소방서', region: '인천광역시', city: '남동구' },
    { id: 55, name: '인천부평소방서', region: '인천광역시', city: '부평구' },
    { id: 56, name: '인천계양소방서', region: '인천광역시', city: '계양구' },
    { id: 57, name: '인천서구소방서', region: '인천광역시', city: '서구' },
    { id: 58, name: '인천강화소방서', region: '인천광역시', city: '강화군' },
    { id: 59, name: '인천옹진소방서', region: '인천광역시', city: '옹진군' },
    
    // 광주광역시 (5개 구)
    { id: 60, name: '광주동구소방서', region: '광주광역시', city: '동구' },
    { id: 61, name: '광주서구소방서', region: '광주광역시', city: '서구' },
    { id: 62, name: '광주남구소방서', region: '광주광역시', city: '남구' },
    { id: 63, name: '광주북구소방서', region: '광주광역시', city: '북구' },
    { id: 64, name: '광주광산소방서', region: '광주광역시', city: '광산구' },
    
    // 대전광역시 (5개 구)
    { id: 65, name: '대전동구소방서', region: '대전광역시', city: '동구' },
    { id: 66, name: '대전중구소방서', region: '대전광역시', city: '중구' },
    { id: 67, name: '대전서구소방서', region: '대전광역시', city: '서구' },
    { id: 68, name: '대전유성소방서', region: '대전광역시', city: '유성구' },
    { id: 69, name: '대전대덕소방서', region: '대전광역시', city: '대덕구' },
    
    // 울산광역시 (5개 구·군)
    { id: 70, name: '울산중구소방서', region: '울산광역시', city: '중구' },
    { id: 71, name: '울산남구소방서', region: '울산광역시', city: '남구' },
    { id: 72, name: '울산동구소방서', region: '울산광역시', city: '동구' },
    { id: 73, name: '울산북구소방서', region: '울산광역시', city: '북구' },
    { id: 74, name: '울산울주소방서', region: '울산광역시', city: '울주군' },
    
    // 세종특별자치시
    { id: 75, name: '세종소방서', region: '세종특별자치시', city: '세종시' },
    
    // 경기도 (주요 시·군 일부)
    { id: 76, name: '경기수원소방서', region: '경기도', city: '수원시' },
    { id: 77, name: '경기성남소방서', region: '경기도', city: '성남시' },
    { id: 78, name: '경기안양소방서', region: '경기도', city: '안양시' },
    { id: 79, name: '경기부천소방서', region: '경기도', city: '부천시' },
    { id: 80, name: '경기광명소방서', region: '경기도', city: '광명시' },
    { id: 81, name: '경기평택소방서', region: '경기도', city: '평택시' },
    { id: 82, name: '경기동두천소방서', region: '경기도', city: '동두천시' },
    { id: 83, name: '경기안산소방서', region: '경기도', city: '안산시' },
    { id: 84, name: '경기고양소방서', region: '경기도', city: '고양시' },
    { id: 85, name: '경기과천소방서', region: '경기도', city: '과천시' },
    { id: 86, name: '경기구리소방서', region: '경기도', city: '구리시' },
    { id: 87, name: '경기남양주소방서', region: '경기도', city: '남양주시' },
    { id: 88, name: '경기오산소방서', region: '경기도', city: '오산시' },
    { id: 89, name: '경기시흥소방서', region: '경기도', city: '시흥시' },
    { id: 90, name: '경기군포소방서', region: '경기도', city: '군포시' },
    { id: 91, name: '경기의왕소방서', region: '경기도', city: '의왕시' },
    { id: 92, name: '경기하남소방서', region: '경기도', city: '하남시' },
    { id: 93, name: '경기용인소방서', region: '경기도', city: '용인시' },
    { id: 94, name: '경기파주소방서', region: '경기도', city: '파주시' },
    { id: 95, name: '경기이천소방서', region: '경기도', city: '이천시' },
    { id: 96, name: '경기안성소방서', region: '경기도', city: '안성시' },
    { id: 97, name: '경기김포소방서', region: '경기도', city: '김포시' },
    { id: 98, name: '경기화성소방서', region: '경기도', city: '화성시' },
    { id: 99, name: '경기광주소방서', region: '경기도', city: '광주시' },
    { id: 100, name: '경기양주소방서', region: '경기도', city: '양주시' },
    
    // 강원특별자치도 (주요 시·군)
    { id: 101, name: '강원춘천소방서', region: '강원특별자치도', city: '춘천시' },
    { id: 102, name: '강원원주소방서', region: '강원특별자치도', city: '원주시' },
    { id: 103, name: '강원강릉소방서', region: '강원특별자치도', city: '강릉시' },
    { id: 104, name: '강원동해소방서', region: '강원특별자치도', city: '동해시' },
    { id: 105, name: '강원태백소방서', region: '강원특별자치도', city: '태백시' },
    { id: 106, name: '강원속초소방서', region: '강원특별자치도', city: '속초시' },
    { id: 107, name: '강원삼척소방서', region: '강원특별자치도', city: '삼척시' },
    { id: 108, name: '강원홍천소방서', region: '강원특별자치도', city: '홍천군' },
    { id: 109, name: '강원횡성소방서', region: '강원특별자치도', city: '횡성군' },
    { id: 110, name: '강원영월소방서', region: '강원특별자치도', city: '영월군' },
    { id: 111, name: '강원평창소방서', region: '강원특별자치도', city: '평창군' },
    { id: 112, name: '강원정선소방서', region: '강원특별자치도', city: '정선군' },
    { id: 113, name: '강원철원소방서', region: '강원특별자치도', city: '철원군' },
    { id: 114, name: '강원화천소방서', region: '강원특별자치도', city: '화천군' },
    { id: 115, name: '강원양구소방서', region: '강원특별자치도', city: '양구군' },
    { id: 116, name: '강원인제소방서', region: '강원특별자치도', city: '인제군' },
    { id: 117, name: '강원고성소방서', region: '강원특별자치도', city: '고성군' },
    { id: 118, name: '강원양양소방서', region: '강원특별자치도', city: '양양군' },
    
    // 충청북도 (주요 시·군)
    { id: 119, name: '충북청주소방서', region: '충청북도', city: '청주시' },
    { id: 120, name: '충북충주소방서', region: '충청북도', city: '충주시' },
    { id: 121, name: '충북제천소방서', region: '충청북도', city: '제천시' },
    { id: 122, name: '충북보은소방서', region: '충청북도', city: '보은군' },
    { id: 123, name: '충북옥천소방서', region: '충청북도', city: '옥천군' },
    { id: 124, name: '충북영동소방서', region: '충청북도', city: '영동군' },
    { id: 125, name: '충북증평소방서', region: '충청북도', city: '증평군' },
    { id: 126, name: '충북진천소방서', region: '충청북도', city: '진천군' },
    { id: 127, name: '충북괴산소방서', region: '충청북도', city: '괴산군' },
    { id: 128, name: '충북음성소방서', region: '충청북도', city: '음성군' },
    { id: 129, name: '충북단양소방서', region: '충청북도', city: '단양군' },
    
    // 충청남도 (주요 시·군)
    { id: 130, name: '충남천안소방서', region: '충청남도', city: '천안시' },
    { id: 131, name: '충남공주소방서', region: '충청남도', city: '공주시' },
    { id: 132, name: '충남보령소방서', region: '충청남도', city: '보령시' },
    { id: 133, name: '충남아산소방서', region: '충청남도', city: '아산시' },
    { id: 134, name: '충남서산소방서', region: '충청남도', city: '서산시' },
    { id: 135, name: '충남논산소방서', region: '충청남도', city: '논산시' },
    { id: 136, name: '충남계룡소방서', region: '충청남도', city: '계룡시' },
    { id: 137, name: '충남당진소방서', region: '충청남도', city: '당진시' },
    { id: 138, name: '충남금산소방서', region: '충청남도', city: '금산군' },
    { id: 139, name: '충남부여소방서', region: '충청남도', city: '부여군' },
    { id: 140, name: '충남서천소방서', region: '충청남도', city: '서천군' },
    { id: 141, name: '충남청양소방서', region: '충청남도', city: '청양군' },
    { id: 142, name: '충남홍성소방서', region: '충청남도', city: '홍성군' },
    { id: 143, name: '충남예산소방서', region: '충청남도', city: '예산군' },
    { id: 144, name: '충남태안소방서', region: '충청남도', city: '태안군' },
    
    // 전라북도 (주요 시·군)
    { id: 145, name: '전북전주소방서', region: '전라북도', city: '전주시' },
    { id: 146, name: '전북군산소방서', region: '전라북도', city: '군산시' },
    { id: 147, name: '전북익산소방서', region: '전라북도', city: '익산시' },
    { id: 148, name: '전북정읍소방서', region: '전라북도', city: '정읍시' },
    { id: 149, name: '전북남원소방서', region: '전라북도', city: '남원시' },
    { id: 150, name: '전북김제소방서', region: '전라북도', city: '김제시' },
    { id: 151, name: '전북완주소방서', region: '전라북도', city: '완주군' },
    { id: 152, name: '전북진안소방서', region: '전라북도', city: '진안군' },
    { id: 153, name: '전북무주소방서', region: '전라북도', city: '무주군' },
    { id: 154, name: '전북장수소방서', region: '전라북도', city: '장수군' },
    { id: 155, name: '전북임실소방서', region: '전라북도', city: '임실군' },
    { id: 156, name: '전북순창소방서', region: '전라북도', city: '순창군' },
    { id: 157, name: '전북고창소방서', region: '전라북도', city: '고창군' },
    { id: 158, name: '전북부안소방서', region: '전라북도', city: '부안군' },
    
    // 전라남도 (주요 시·군)
    { id: 159, name: '전남목포소방서', region: '전라남도', city: '목포시' },
    { id: 160, name: '전남여수소방서', region: '전라남도', city: '여수시' },
    { id: 161, name: '전남순천소방서', region: '전라남도', city: '순천시' },
    { id: 162, name: '전남나주소방서', region: '전라남도', city: '나주시' },
    { id: 163, name: '전남광양소방서', region: '전라남도', city: '광양시' },
    { id: 164, name: '전남담양소방서', region: '전라남도', city: '담양군' },
    { id: 165, name: '전남곡성소방서', region: '전라남도', city: '곡성군' },
    { id: 166, name: '전남구례소방서', region: '전라남도', city: '구례군' },
    { id: 167, name: '전남고흥소방서', region: '전라남도', city: '고흥군' },
    { id: 168, name: '전남보성소방서', region: '전라남도', city: '보성군' },
    { id: 169, name: '전남화순소방서', region: '전라남도', city: '화순군' },
    { id: 170, name: '전남장흥소방서', region: '전라남도', city: '장흥군' },
    { id: 171, name: '전남강진소방서', region: '전라남도', city: '강진군' },
    { id: 172, name: '전남해남소방서', region: '전라남도', city: '해남군' },
    { id: 173, name: '전남영암소방서', region: '전라남도', city: '영암군' },
    { id: 174, name: '전남무안소방서', region: '전라남도', city: '무안군' },
    { id: 175, name: '전남함평소방서', region: '전라남도', city: '함평군' },
    { id: 176, name: '전남영광소방서', region: '전라남도', city: '영광군' },
    { id: 177, name: '전남장성소방서', region: '전라남도', city: '장성군' },
    { id: 178, name: '전남완도소방서', region: '전라남도', city: '완도군' },
    { id: 179, name: '전남진도소방서', region: '전라남도', city: '진도군' },
    { id: 180, name: '전남신안소방서', region: '전라남도', city: '신안군' },
    
    // 경상북도 (주요 시·군)
    { id: 181, name: '경북포항소방서', region: '경상북도', city: '포항시' },
    { id: 182, name: '경북경주소방서', region: '경상북도', city: '경주시' },
    { id: 183, name: '경북김천소방서', region: '경상북도', city: '김천시' },
    { id: 184, name: '경북안동소방서', region: '경상북도', city: '안동시' },
    { id: 185, name: '경북구미소방서', region: '경상북도', city: '구미시' },
    { id: 186, name: '경북영주소방서', region: '경상북도', city: '영주시' },
    { id: 187, name: '경북영천소방서', region: '경상북도', city: '영천시' },
    { id: 188, name: '경북상주소방서', region: '경상북도', city: '상주시' },
    { id: 189, name: '경북문경소방서', region: '경상북도', city: '문경시' },
    { id: 190, name: '경북경산소방서', region: '경상북도', city: '경산시' },
    { id: 191, name: '경북군위소방서', region: '경상북도', city: '군위군' },
    { id: 192, name: '경북의성소방서', region: '경상북도', city: '의성군' },
    { id: 193, name: '경북청송소방서', region: '경상북도', city: '청송군' },
    { id: 194, name: '경북영양소방서', region: '경상북도', city: '영양군' },
    { id: 195, name: '경북영덕소방서', region: '경상북도', city: '영덕군' },
    { id: 196, name: '경북청도소방서', region: '경상북도', city: '청도군' },
    { id: 197, name: '경북고령소방서', region: '경상북도', city: '고령군' },
    { id: 198, name: '경북성주소방서', region: '경상북도', city: '성주군' },
    { id: 199, name: '경북칠곡소방서', region: '경상북도', city: '칠곡군' },
    { id: 200, name: '경북예천소방서', region: '경상북도', city: '예천군' },
    { id: 201, name: '경북봉화소방서', region: '경상북도', city: '봉화군' },
    { id: 202, name: '경북울진소방서', region: '경상북도', city: '울진군' },
    { id: 203, name: '경북울릉소방서', region: '경상북도', city: '울릉군' },
    
    // 경상남도 (주요 시·군)
    { id: 204, name: '경남창원소방서', region: '경상남도', city: '창원시' },
    { id: 205, name: '경남진주소방서', region: '경상남도', city: '진주시' },
    { id: 206, name: '경남통영소방서', region: '경상남도', city: '통영시' },
    { id: 207, name: '경남사천소방서', region: '경상남도', city: '사천시' },
    { id: 208, name: '경남김해소방서', region: '경상남도', city: '김해시' },
    { id: 209, name: '경남밀양소방서', region: '경상남도', city: '밀양시' },
    { id: 210, name: '경남거제소방서', region: '경상남도', city: '거제시' },
    { id: 211, name: '경남양산소방서', region: '경상남도', city: '양산시' },
    { id: 212, name: '경남의령소방서', region: '경상남도', city: '의령군' },
    { id: 213, name: '경남함안소방서', region: '경상남도', city: '함안군' },
    { id: 214, name: '경남창녕소방서', region: '경상남도', city: '창녕군' },
    { id: 215, name: '경남고성소방서', region: '경상남도', city: '고성군' },
    { id: 216, name: '경남남해소방서', region: '경상남도', city: '남해군' },
    { id: 217, name: '경남하동소방서', region: '경상남도', city: '하동군' },
    { id: 218, name: '경남산청소방서', region: '경상남도', city: '산청군' },
    { id: 219, name: '경남함양소방서', region: '경상남도', city: '함양군' },
    { id: 220, name: '경남거창소방서', region: '경상남도', city: '거창군' },
    { id: 221, name: '경남합천소방서', region: '경상남도', city: '합천군' },
    
    // 제주특별자치도
    { id: 222, name: '제주제주소방서', region: '제주특별자치도', city: '제주시' },
    { id: 223, name: '제주서귀포소방서', region: '제주특별자치도', city: '서귀포시' }
  ];

  // 지역별 소방서 필터링
  const getFireStationsByRegion = (region: string) => {
    return allFireStations.filter((station) => station.region === region);
  };

  // 검색된 소방서 필터링
  const getFilteredStations = () => {
    if (selectedRegion !== '전국') {
      const regionStations = getFireStationsByRegion(selectedRegion);
      if (searchStation) {
        return regionStations.filter(station =>
          station.name.toLowerCase().includes(searchStation.toLowerCase()) ||
          station.city.toLowerCase().includes(searchStation.toLowerCase())
        );
      }
      return regionStations;
    }
    
    if (searchStation) {
      return allFireStations.filter(station =>
        station.name.toLowerCase().includes(searchStation.toLowerCase()) ||
        station.region.toLowerCase().includes(searchStation.toLowerCase()) ||
        station.city.toLowerCase().includes(searchStation.toLowerCase())
      );
    }
    
    return allFireStations;
  };

  // 내 위치 기반 추천 소방서
  const getNearbyFireStations = () => {
    return [
      {
        id: 1,
        name: '서울중구소방서',
        region: '서울특별시',
        city: '중구',
        distance: '1.2km',
        todayDispatch: 8,
        todayFires: 3,
      },
      {
        id: 2,
        name: '서울강남소방서',
        region: '서울특별시',
        city: '강남구',
        distance: '2.8km',
        todayDispatch: 12,
        todayFires: 2,
      },
      {
        id: 3,
        name: '서울서초소방서',
        region: '서울특별시',
        city: '서초구',
        distance: '3.5km',
        todayDispatch: 6,
        todayFires: 1,
      }
    ];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case '진압중': return 'bg-red-100 text-red-800';
      case '출동중': return 'bg-orange-100 text-orange-800';
      case '현장도착': return 'bg-yellow-100 text-yellow-800';
      case '구조완료': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // 출동 건수에 따른 색상 반환 함수
  const getEmergencyColor = (count: number) => {
    if (count >= 15) return 'text-red-600 font-semibold';
    if (count >= 10) return 'text-orange-500 font-medium';
    if (count >= 5) return 'text-yellow-600 font-medium';
    return 'text-green-600';
  };

  // 화재 건수에 따른 색상 반환 함수
  const getFireColor = (count: number) => {
    if (count >= 8) return 'text-red-600 font-semibold';
    if (count >= 5) return 'text-orange-500 font-medium';
    if (count >= 2) return 'text-yellow-600 font-medium';
    return 'text-green-600';
  };

  const handleRegionClick = (region: any) => {
    setSelectedRegionData(region);
    setShowRegionDetail(true);
  };

  const handleDonateClick = (stationName: string) => {
    router.push(`/donations?station=${encodeURIComponent(stationName)}`);
  };

  // 복수 기부 관련 핸들러
  const handleMultipleDonationClick = () => {
    setTempSelectedStations([]);
    setSelectedFireStations([]);
    setShowMultipleDonationModal(true);
  };

  const handleTempStationSelect = (stationName: string) => {
    if (tempSelectedStations.includes(stationName)) {
      setTempSelectedStations(prev => prev.filter(s => s !== stationName));
    } else {
      setTempSelectedStations(prev => [...prev, stationName]);
    }
  };

  const handleSelectAllStations = () => {
    if (selectAllStations) {
      setTempSelectedStations([]);
      setSelectAllStations(false);
    } else {
      const allStationNames = getFilteredStations().map(station => station.name);
      setTempSelectedStations(allStationNames);
      setSelectAllStations(true);
    }
  };

  const handleSelectRegionStations = (region: string) => {
    const regionStations = getFireStationsByRegion(region).map(station => station.name);
    const newSelected = [...new Set([...tempSelectedStations, ...regionStations])];
    setTempSelectedStations(newSelected);
    setShowRegionModal(false);
  };

  const handleLocationSelect = () => {
    setShowLocationModal(true);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          console.log('위치 정보:', position.coords);
          const nearbyStations = getNearbyFireStations().map(station => station.name);
          setTempSelectedStations(prev => [...new Set([...prev, ...nearbyStations])]);
          setShowLocationModal(false);
        },
        (error) => {
          console.error('위치 정보 가져오기 실패:', error);
          alert('위치 정보를 가져올 수 없습니다. 권한을 확인해주세요.');
          setShowLocationModal(false);
        }
      );
    } else {
      alert('위치 서비스가 지원되지 않는 브라우저입니다.');
      setShowLocationModal(false);
    }
  };

  const handleConfirmMultipleDonation = () => {
    if (tempSelectedStations.length === 0) {
      alert('최소 1개 이상의 소방서를 선택해주세요.');
      return;
    }
    
    setSelectedFireStations([...tempSelectedStations]);
    const stationsParam = tempSelectedStations.join(',');
    const typeParam = donationType;
    
    router.push(`/donations?stations=${encodeURIComponent(stationsParam)}&type=${typeParam}`);
  };

  // 지역별 상세 소방서 데이터
  const detailedFireStations: { [key: string]: any[] } = {};

  // 각 지역별로 상세 소방서 데이터 생성
  fireStationsByRegion.forEach(regionData => {
    const stations = getFireStationsByRegion(regionData.region);
    detailedFireStations[regionData.region] = stations.map(station => ({
      ...station,
      fireReport: Math.floor(Math.random() * 15) + 1,
      onDuty: Math.floor(Math.random() * 3),
      suppressing: Math.floor(Math.random() * 2)
    }));
  });

  return (
    <div className="bg-gray-50">
      <section className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* 페이지 헤더 */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">전국 소방서 현황</h1>
            <p className="text-lg text-gray-600">실시간 소방서 운영 현황과 출동 상황을 확인하세요</p>
          </div>

          {/* 필터 */}
          <div className="mb-8 flex flex-wrap gap-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-707">지역:</span>
              <select 
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm pr-8"
              >
                {regions.map(region => (
                  <option key={region} value={region}>{region}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-707">상태:</span>
              <select 
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm pr-8"
              >
                {statusTypes.map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>
            
            {/* 복수 기부 버튼 추가 */}
            <div className="ml-auto">
              <Button
                onClick={handleMultipleDonationClick}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                <i className="ri-heart-line mr-2"></i>
                여러 소방서에 기부하기
              </Button>
            </div>
          </div>

          {/* 전체 현황 통계 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">{totalStats.totalStations.toLocaleString()}</div>
              <div className="text-sm text-gray-600">총 소방서</div>
            </Card>
            <Card className="text-center">
              <div className="text-2xl font-bold text-green-600 mb-1">{totalStats.fireReportStations.toLocaleString()}</div>
              <div className="text-sm text-gray-600">화재접수</div>
            </Card>
            <Card className="text-center">
              <div className="text-2xl font-bold text-orange-600 mb-1">{totalStats.onDutyStations}</div>
              <div className="text-sm text-gray-600">출동 중</div>
            </Card>
            <Card className="text-center">
              <div className="text-2xl font-bold text-red-600 mb-1">{totalStats.suppressingStations}</div>
              <div className="text-sm text-gray-600">진압 중</div>
            </Card>
          </div>

          {/* 실시간 출동 현황 */}
          <Card className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">실시간 출동 현황</h3>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-red-600 font-medium">실시간 업데이트</span>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">지역</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">소방서</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">위치</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">상태</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">시간</th>
                  </tr>
                </thead>
                <tbody>
                  {emergencyIncidents.map((incident, index) => (
                    <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">{incident.region}</td>
                      <td className="py-3 px-4 text-gray-700">{incident.station}</td>
                      <td className="py-3 px-4 text-gray-600 text-sm">{incident.location}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(incident.status)}`}>
                          {incident.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-gray-500 text-sm">{incident.time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* 월별 출동 현황 */}
          <Card className="mb-8">
            <h3 className="text-lg font-bold text-gray-900 mb-4">월별 출동 현황</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">구분</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">출동 건수</th>
                  </tr>
                </thead>
                <tbody>
                  {monthlyStats.map((stat, index) => (
                    <tr key={index} className="border-b border-gray-100">
                      <td className="py-3 px-4 font-medium text-gray-900">{stat.month}</td>
                      <td className="py-3 px-4 text-right text-gray-700">{stat.incidents.toLocaleString()}건</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* 지역별 소방서 현황 */}
          <Card>
            <h3 className="text-lg font-bold text-gray-900 mb-4">지역별 소방서 현황</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">지역</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-900">총 소방서</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-900">화재접수</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-900">출동 중</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-900">진압 중</th>
                    <th className="text-center py-3 px-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {fireStationsByRegion.map((region, index) => (
                    <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">{region.region}</td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => handleRegionClick(region)}
                          className="text-gray-700 hover:text-blue-600 hover:underline cursor-pointer"
                        >
                          {region.total}
                        </button>
                      </td>
                      <td className="py-3 px-4 text-center text-green-600">{region.fireReport}</td>
                      <td className="py-3 px-4 text-center text-orange-600">{region.onDuty}</td>
                      <td className="py-3 px-4 text-center text-red-600">{region.suppressing}</td>
                      <td className="py-3 px-4 text-center">
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="text-xs whitespace-nowrap"
                          onClick={() => handleRegionClick(region)}
                        >
                          <i className="ri-heart-line mr-1"></i>
                          기부하기
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

        </div>
      </section>

      {/* 복수 소방서 기부 모달 */}
      {showMultipleDonationModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-6xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">여러 소방서에 기부하기</h3>
                <p className="text-gray-600">기부할 소방서들을 선택하고 기부 방식을 정해주세요</p>
              </div>
              <button
                onClick={() => setShowMultipleDonationModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>

            {/* 기부 방식 선택 */}
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-3">기부 방식 선택</h4>
              <div className="space-y-3">
                <label className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="donationType"
                    value="split"
                    checked={donationType === 'split'}
                    onChange={(e) => setDonationType(e.target.value as 'split' | 'each')}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500 mt-0.5"
                  />
                  <div>
                    <span className="text-blue-900 font-medium">분할 기부</span>
                    <p className="text-sm text-blue-700">선택한 금액을 소방서 수로 나누어 기부</p>
                  </div>
                </label>
                <label className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="donationType"
                    value="each"
                    checked={donationType === 'each'}
                    onChange={(e) => setDonationType(e.target.value as 'split' | 'each')}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500 mt-0.5"
                  />
                  <div>
                    <span className="text-blue-900 font-medium">각각 기부</span>
                    <p className="text-sm text-blue-700">선택한 모든 소방서에 해당 금액씩 기부</p>
                  </div>
                </label>
              </div>
            </div>

            {/* 선택 옵션 */}
            <div className="mb-6 flex flex-wrap gap-4">
              <button
                onClick={handleSelectAllStations}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors duration-200"
              >
                <i className="ri-checkbox-multiple-line mr-2"></i>
                {selectAllStations ? '전체 해제' : '전체 선택'}
              </button>
              
              <button
                onClick={() => setShowRegionModal(true)}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors duration-200"
              >
                <i className="ri-map-pin-line mr-2"></i>
                지역별 선택
              </button>
              
              <button
                onClick={handleLocationSelect}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors duration-200"
              >
                <i className="ri-navigation-line mr-2"></i>
                내 위치 주변
              </button>
            </div>

            {/* 검색 */}
            <div className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  value={searchStation}
                  onChange={(e) => setSearchStation(e.target.value)}
                  placeholder="소방서명이나 지역명을 입력하세요"
                  className="w-full px-4 py-3 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm"
                />
                <i className="ri-search-line absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
              </div>
            </div>

            {/* 선택된 소방서 표시 */}
            {tempSelectedStations.length > 0 && (
              <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-blue-900">
                    선택된 소방서: {tempSelectedStations.length}개
                  </span>
                  <button
                    onClick={() => setTempSelectedStations([])}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    전체 해제
                  </button>
                </div>
                <div className="flex flex-wrap gap-2 max-h-20 overflow-y-auto">
                  {tempSelectedStations.map((station, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
                    >
                      {station}
                      <button
                        onClick={() => setTempSelectedStations(prev => prev.filter(s => s !== station))}
                        className="ml-1 text-blue-600 hover:text-blue-800"
                      >
                        <i className="ri-close-line text-sm"></i>
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 소방서 목록 */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="max-h-96 overflow-y-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="w-12 px-4 py-3 text-left">
                        <input
                          type="checkbox"
                          checked={tempSelectedStations.length === getFilteredStations().length && getFilteredStations().length > 0}
                          onChange={handleSelectAllStations}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">소방서명</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">지역</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">오늘 출동</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">화재</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {getFilteredStations().map((station) => {
                      const todayDispatch = Math.floor(Math.random() * 15) + 1;
                      const todayFires = Math.floor(Math.random() * 5) + 1;
                      const isSelected = tempSelectedStations.includes(station.name);
                      
                      return (
                        <tr 
                          key={station.id} 
                          className={`hover:bg-gray-50 cursor-pointer transition-colors duration-200 ${
                            isSelected ? 'bg-blue-50' : ''
                          }`}
                          onClick={() => handleTempStationSelect(station.name)}
                        >
                          <td className="px-4 py-3">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleTempStationSelect(station.name)}
                              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            />
                          </td>
                          <td className="px-4 py-3 font-medium text-gray-900">{station.name}</td>
                          <td className="px-4 py-3 text-gray-600">{station.region} {station.city}</td>
                          <td className="px-4 py-3 text-center">
                            <span className={getEmergencyColor(todayDispatch)}>
                              {todayDispatch}건
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={getFireColor(todayFires)}>
                              {todayFires}건
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 확인 버튼 */}
            <div className="mt-6 flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => setShowMultipleDonationModal(false)}
              >
                취소
              </Button>
              <Button
                onClick={handleConfirmMultipleDonation}
                disabled={tempSelectedStations.length === 0}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                기부하기 ({tempSelectedStations.length}개 선택)
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 지역별 선택 모달 */}
      {showRegionModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-4xl mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">지역별 소방서 선택</h3>
                <p className="text-gray-600">지역을 선택하면 해당 지역의 모든 소방서가 추가됩니다</p>
              </div>
              <button
                onClick={() => setShowRegionModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {regions.slice(1).map((region) => { // '전국' 제외
                const regionStations = getFireStationsByRegion(region);
                const selectedCount = regionStations.filter(station => 
                  tempSelectedStations.includes(station.name)
                ).length;
                
                return (
                  <button
                    key={region}
                    onClick={() => handleSelectRegionStations(region)}
                    className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 text-left"
                  >
                    <div className="font-medium text-gray-900 mb-1">{region}</div>
                    <div className="text-sm text-gray-500">
                      {regionStations.length}개 소방서
                    </div>
                    {selectedCount > 0 && (
                      <div className="text-xs text-blue-600 mt-1">
                        {selectedCount}개 선택됨
                      </div>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="mt-6 flex justify-end">
              <Button
                variant="outline"
                onClick={() => setShowRegionModal(false)}
              >
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 위치 기반 선택 모달 */}
      {showLocationModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-navigation-line text-purple-500 text-3xl animate-pulse"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">위치 확인 중</h3>
              <p className="text-gray-600 mb-4">현재 위치를 기반으로 주변 소방서를 찾고 있습니다...</p>
              <Button
                variant="outline"
                onClick={() => setShowLocationModal(false)}
              >
                취소
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 지역별 상세 소방서 모달 */}
      {showRegionDetail && selectedRegionData && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-6xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">
                  {selectedRegionData.region} 소방서 현황
                </h3>
                <p className="text-gray-600 mt-1">
                  총 {selectedRegionData.total}개 소방서 • 화재접수 {selectedRegionData.fireReport}개 • 출동중 {selectedRegionData.onDuty}개 • 진압중 {selectedRegionData.suppressing}개
                </p>
              </div>
              <button
                onClick={() => setShowRegionDetail(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200 bg-gray-50">
                    <th className="text-left py-4 px-4 font-semibold text-gray-900">소방서명</th>
                    <th className="text-left py-4 px-4 font-semibold text-gray-900">지역</th>
                    <th className="text-center py-4 px-4 font-semibold text-gray-900">화재접수</th>
                    <th className="text-center py-4 px-4 font-semibold text-gray-900">출동중</th>
                    <th className="text-center py-4 px-4 font-semibold text-gray-900">진압중</th>
                    <th className="text-center py-4 px-4 font-semibold text-gray-900">지원하기</th>
                  </tr>
                </thead>
                <tbody>
                  {detailedFireStations[selectedRegionData.region]?.map((station, index) => (
                    <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-4 px-4 font-medium text-gray-900">{station.name}</td>
                      <td className="py-4 px-4 text-gray-600">{station.city}</td>
                      <td className="py-4 px-4 text-center">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {station.fireReport}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-center">
                        {station.onDuty > 0 ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                            {station.onDuty}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="py-4 px-4 text-center">
                        {station.suppressing > 0 ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            {station.suppressing}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="py-4 px-4 text-center">
                        <Button 
                          size="sm" 
                          variant="donate" 
                          className="text-xs whitespace-nowrap ml-2"
                          onClick={() => {
                            setShowRegionDetail(false);
                            handleDonateClick(station.name);
                          }}
                        >
                          <i className="ri-heart-fill mr-1"></i>
                          기부하기
                        </Button>
                      </td>
                    </tr>
                  )) || (
                    <tr>
                      <td colSpan={6} className="py-8 px-4 text-center text-gray-500">
                        해당 지역의 상세 소방서 정보가 없습니다.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="mt-8 flex justify-center">
              <Button 
                variant="outline" 
                onClick={() => setShowRegionDetail(false)}
                className="px-8"
              >
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
