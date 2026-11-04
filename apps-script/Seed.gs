/**
 * 기존 기록장(Claude) 기록을 새 시트로 옮기는 파일. 처음에 seed를 한 번만 실행한다.
 * 다시 실행하면 같은 날짜는 이 내용으로 덮어쓴다(전환하는 날 최신으로 다시 만들어 쓸 수 있다).
 */
const SEED = {
 "days/2026-11-02": {
  "condition": null,
  "date": "2026-11-02",
  "logs": [
   {
    "hours": 4,
    "kind": "자습",
    "note": "",
    "start": "14:30",
    "subject": "미적"
   }
  ],
  "sleep": 11.5,
  "spans": [
   [
    "00:00",
    "08:00",
    "수면",
    "sleep"
   ],
   [
    "14:30",
    "18:30",
    "미적",
    "study"
   ],
   [
    "20:30",
    "24:00",
    "수면",
    "sleep"
   ]
  ]
 },
 "days/2026-11-03": {
  "condition": null,
  "date": "2026-11-03",
  "logs": [
   {
    "hours": 1.5,
    "kind": "자습",
    "note": "",
    "start": "17:00",
    "subject": "미적"
   },
   {
    "hours": 1.5,
    "kind": "자습",
    "note": "",
    "start": "18:30",
    "subject": "영어"
   },
   {
    "hours": 1.5,
    "kind": "운동",
    "note": "등",
    "start": "20:00",
    "subject": ""
   },
   {
    "hours": 2.5,
    "kind": "자습",
    "note": "",
    "start": "21:30",
    "subject": "물리"
   }
  ],
  "sleep": 7.5,
  "spans": [
   [
    "00:00",
    "07:30",
    "수면",
    "sleep"
   ],
   [
    "17:00",
    "18:30",
    "미적",
    "study"
   ],
   [
    "18:30",
    "20:00",
    "영어",
    "study"
   ],
   [
    "20:00",
    "21:30",
    "등",
    "other"
   ],
   [
    "21:30",
    "24:00",
    "물리",
    "study"
   ]
  ]
 },
 "days/2026-11-04": {
  "condition": null,
  "date": "2026-11-04",
  "logs": [
   {
    "hours": 1.5,
    "kind": "자습",
    "note": "",
    "start": "16:30",
    "subject": "미적"
   },
   {
    "hours": 1.5,
    "kind": "운동",
    "note": "가슴",
    "start": "18:00",
    "subject": ""
   },
   {
    "hours": 2.5,
    "kind": "자습",
    "note": "",
    "start": "19:30",
    "subject": "영어"
   }
  ],
  "sleep": 4.5,
  "spans": [
   [
    "01:30",
    "06:00",
    "수면",
    "sleep"
   ],
   [
    "16:30",
    "18:00",
    "미적",
    "study"
   ],
   [
    "18:00",
    "19:30",
    "가슴",
    "other"
   ],
   [
    "19:30",
    "22:00",
    "영어",
    "study"
   ]
  ]
 },
 "days/2026-11-05": {
  "condition": null,
  "date": "2026-11-05",
  "logs": [],
  "sleep": 7.5,
  "spans": [
   [
    "00:00",
    "07:30",
    "수면",
    "sleep"
   ],
   [
    "17:00",
    "18:00",
    "피부과가기",
    "plan-other"
   ]
  ]
 },
 "days/2026-11-06": {
  "condition": null,
  "date": "2026-11-06",
  "logs": [],
  "sleep": null,
  "spans": []
 },
 "days/2026-11-07": {
  "condition": null,
  "date": "2026-11-07",
  "logs": [],
  "sleep": null,
  "spans": []
 },
 "days/2026-11-08": {
  "condition": null,
  "date": "2026-11-08",
  "logs": [],
  "sleep": null,
  "spans": []
 },
 "plan/exams": {
  "items": [
   {
    "date": "2026-12-14",
    "subject": "기말",
    "unitsDone": 0,
    "unitsTotal": 0
   }
  ]
 },
 "plan/labels": {
  "items": [
   {
    "kind": "기타",
    "t": "피부과가기",
    "type": "other"
   }
  ]
 },
 "plan/tasks": {
  "items": [
   {
    "date": "2026-11-05",
    "subject": "",
    "title": "도시락통·단백질통 위치 찾기"
   },
   {
    "date": "2026-11-11",
    "subject": "",
    "title": "이무현 책 가져오기 (새로운 두 과학)"
   },
   {
    "date": "",
    "subject": "",
    "title": "공부기록장에 저번주 노트 찍어 올리기"
   }
  ]
 },
 "plan/timetable": {
  "items": [
   {
    "day": "월",
    "end": "18:30",
    "kind": "학원",
    "start": "17:00",
    "title": "수학"
   },
   {
    "day": "수",
    "end": "17:30",
    "kind": "학원",
    "start": "16:00",
    "title": "수학"
   },
   {
    "day": "금",
    "end": "18:30",
    "kind": "학원",
    "start": "17:00",
    "title": "수학"
   },
   {
    "day": "화",
    "end": "20:00",
    "kind": "학원",
    "start": "18:30",
    "title": "영어"
   },
   {
    "day": "목",
    "end": "20:00",
    "kind": "학원",
    "start": "18:30",
    "title": "영어"
   },
   {
    "day": "금",
    "end": "20:00",
    "kind": "학원",
    "start": "18:30",
    "title": "영어"
   },
   {
    "day": "월",
    "end": "20:00",
    "kind": "운동",
    "start": "18:30",
    "title": "운동"
   },
   {
    "day": "화",
    "end": "21:30",
    "kind": "운동",
    "start": "20:00",
    "title": "운동"
   },
   {
    "day": "수",
    "end": "19:00",
    "kind": "운동",
    "start": "17:30",
    "title": "운동"
   },
   {
    "day": "목",
    "end": "21:30",
    "kind": "운동",
    "start": "20:00",
    "title": "운동"
   },
   {
    "day": "금",
    "end": "21:30",
    "kind": "운동",
    "start": "20:00",
    "title": "운동"
   },
   {
    "day": "토",
    "end": "13:30",
    "kind": "운동",
    "start": "12:00",
    "title": "운동"
   },
   {
    "day": "일",
    "end": "13:30",
    "kind": "운동",
    "start": "12:00",
    "title": "운동"
   }
  ]
 },
 "plan/wall": {
  "name": "기말"
 }
};

function seed() {
  writeOps_(Object.keys(SEED).map(key => ({key: key, doc: SEED[key]})));
  Logger.log('옮긴 항목: ' + Object.keys(SEED).length + '개');
}
