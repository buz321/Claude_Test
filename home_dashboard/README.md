# 우리집 대시보드 (home-dashboard)

라즈베리파이 4에 올려놓고 **집 안에서만** 쓰는 가족 공용 웹 대시보드입니다.
집안일·장보기 목록·이번 주 일정을 한 화면에서 보고, **핸드폰으로 푸시 알림**까지 받습니다.

- 서버는 집 공유기 안(LAN)에만 열립니다. 포트포워딩 없이 `http://라즈베리파이IP:8000` 으로 접속.
- 알림은 라즈베리파이가 **밖으로 보내는 방향**이라 외부에 포트를 열 필요가 없습니다.
- 데이터는 SQLite 파일 하나(`home.db`)라 백업이 쉽습니다.

## 화면

| 탭 | 내용 |
|---|---|
| 오늘 | 지난 할일 / 오늘 할일 / 오늘·이번 주 일정 / 살 것 요약 |
| 할일 | 담당자, 마감 날짜·시간, 매일·매주·매월 반복 |
| 장보기 | 수량·급함 표시, 산 것 한 번에 비우기 |
| 일정 | 날짜·시간·장소 |

핸드폰 브라우저에서 **홈 화면에 추가**하면 앱처럼 전체화면으로 뜹니다 (PWA manifest 포함).

## 알림

| 시점 | 내용 |
|---|---|
| 매일 아침(기본 08:00) | 오늘 할일 + 오늘·이번 주 일정 + 살 것 요약 한 통 |
| 할일 마감 시각 | 시간이 지정된 할일이 되면 알림 |
| 일정 시작 전(기본 30분) | 일정 임박 알림 |
| 앱 우측 상단 🔔 | 지금 바로 요약 알림 테스트 |

같은 항목을 두 번 보내지 않도록 발송 기록(`notification_log`)으로 중복을 막습니다.

### 알림 채널 고르기

| 채널 | 준비물 | 특징 |
|---|---|---|
| `ntfy` (추천) | 핸드폰에 [ntfy](https://ntfy.sh) 앱 설치 → 토픽 구독 | 가입 없이 바로 됨. 자체 호스팅도 가능 |
| `telegram` | 텔레그램 봇 토큰 + chat_id | 가족 단톡방에 알림 보내기 좋음 |
| `console` | 없음 | 기본값. 로그로만 출력(설정 전 테스트용) |

> ⚠️ ntfy 토픽 이름은 **비밀번호처럼** 취급하세요. 이름을 아는 사람은 누구나 구독할 수 있습니다.
> `우리집-a7f3k9x2` 처럼 추측하기 어렵게 지으세요.

**텔레그램 chat_id 얻는 법**: [@BotFather](https://t.me/botfather) 로 봇을 만들고 토큰을 받은 뒤,
그 봇에게 아무 메시지나 보내고 `https://api.telegram.org/bot<토큰>/getUpdates` 를 열면 `chat.id` 가 보입니다.

## 라즈베리파이에 설치

```bash
git clone <이 저장소> ~/home_dashboard
cd ~/home_dashboard/home_dashboard
bash deploy/install.sh          # venv 생성 + 의존성 설치 + systemd 등록
nano .env                       # 알림 채널 설정 (아래 표 참고)
sudo systemctl restart home-dashboard
```

설치가 끝나면 부팅할 때마다 자동 실행되고, 죽으면 자동 재시작됩니다.

```bash
sudo systemctl status home-dashboard   # 상태
journalctl -u home-dashboard -f        # 로그 실시간 보기
```

접속: `http://라즈베리파이IP:8000`
(고정 IP를 쓰거나 공유기에서 DHCP 고정 할당을 해두면 편합니다. `raspberrypi.local:8000` 도 보통 됩니다.)

## 직접 실행 (개발/테스트)

```bash
pip install -e ".[dev]"
HOME_DB_PATH=home.db python -m app.main
# 또는
home-dashboard
```

테스트:

```bash
python -m pytest
```

## 설정 (환경변수)

| 변수 | 기본값 | 설명 |
|---|---|---|
| `HOME_DB_PATH` | `home.db` | SQLite 파일 경로 |
| `HOME_HOST` / `HOME_PORT` | `0.0.0.0` / `8000` | 바인딩 주소·포트 |
| `HOME_TZ` | `Asia/Seoul` | 날짜·알림 기준 타임존 |
| `HOME_NOTIFY_CHANNEL` | `console` | `console` / `ntfy` / `telegram` |
| `HOME_NTFY_SERVER` | `https://ntfy.sh` | 자체 호스팅 시 변경 |
| `HOME_NTFY_TOPIC` | – | 구독할 토픽 이름 |
| `HOME_NTFY_TOKEN` | – | 인증을 켠 자체 호스팅 ntfy 용 |
| `HOME_TELEGRAM_TOKEN` / `HOME_TELEGRAM_CHAT_ID` | – | 텔레그램 봇 정보 |
| `HOME_DIGEST_TIME` | `08:00` | 아침 요약 알림 시각 |
| `HOME_EVENT_LEAD_MINUTES` | `30` | 일정 몇 분 전에 알릴지 |
| `HOME_SCHEDULER` | `1` | `0` 이면 알림 스케줄러 끔 |

채널 설정값이 비어 있으면 자동으로 `console` 로 폴백하므로, 잘못된 설정으로 서버가 죽지 않습니다.

## API

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/api/summary` | 오늘 화면에 필요한 데이터 한 번에 |
| `GET` | `/api/health` | 상태 + 현재 알림 채널 |
| `GET/POST` | `/api/tasks` | 할일 목록·추가 |
| `PATCH/DELETE` | `/api/tasks/{id}` | 할일 수정(완료 토글)·삭제 |
| `GET/POST` | `/api/shopping` | 장보기 목록·추가 |
| `PATCH/DELETE` | `/api/shopping/{id}` | 장보기 수정·삭제 |
| `POST` | `/api/shopping/clear-bought` | 산 것 일괄 정리 |
| `GET/POST` | `/api/events` | 일정 목록·추가 |
| `PATCH/DELETE` | `/api/events/{id}` | 일정 수정·삭제 |
| `GET` | `/api/notify/preview` | 요약 알림 문구 미리보기 |
| `POST` | `/api/notify/digest` | 요약 알림 지금 발송 |

FastAPI 자동 문서: `http://라즈베리파이IP:8000/docs`

**반복 할일**은 완료 체크하면 사라지지 않고 다음 주기(다음 날/주/달)로 마감일이 넘어갑니다.
매월 31일처럼 다음 달에 없는 날짜는 그 달 말일로 당깁니다.

## 구조

```
home_dashboard/
├── app/
│   ├── main.py         FastAPI 라우트 + 앱 팩토리
│   ├── config.py       환경변수 설정
│   ├── db.py           SQLite 연결/스키마
│   ├── models.py       요청 스키마(pydantic)
│   ├── repository.py   CRUD + 대시보드 조회
│   ├── notifier.py     ntfy / 텔레그램 / 콘솔 알림 채널
│   ├── digest.py       알림 문구 생성
│   ├── scheduler.py    아침 요약·마감·일정 임박 잡
│   └── static/         모바일 우선 웹 UI (빌드 도구 없이 순수 HTML/CSS/JS)
├── deploy/             systemd 서비스 + 설치 스크립트 + .env 예시
└── tests/              pytest (API 20여 개 시나리오)
```

프런트엔드는 빌드 단계가 없습니다. 라즈베리파이에 Node.js를 깔 필요가 없고,
`static/` 파일만 고치면 새로고침으로 바로 반영됩니다.

## 보안 메모

- 로그인 기능이 없습니다. **집 안 네트워크에서만** 쓰는 것을 전제로 합니다.
  공유기에서 8000번 포트를 외부로 포워딩하지 마세요.
- 밖에서도 쓰고 싶다면 포트포워딩 대신 [Tailscale](https://tailscale.com) 같은 VPN을 붙이는 쪽이 안전합니다.
- 백업은 `home.db` 파일만 복사하면 됩니다 (`sqlite3 home.db ".backup backup.db"` 권장).
