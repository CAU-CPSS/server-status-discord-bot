# 🤖 CPSS Discord Bot

CPSS 연구실 서버 상태를 디스코드에서 확인할 수 있는 봇입니다.<br />
`/status` 명령어를 입력하면 CPU, RAM, GPU 사용 정보, 실행 중인 실험(프로세스) 목록을 확인할 수 있습니다.<br />
실험 시작/종료 시 자동으로 알림이 옵니다.

<img width="1024" height="768" alt="Slide 4_3 - 1" src="https://github.com/user-attachments/assets/40e2deaf-05a7-45fc-a428-0630a007d5f1" />


## 📂 파일 구조

```
discord-bot/
├── status_bot.py
├── .env
├── .gitignore
└── README.md
```

## 🔁 코드 수정 후 재시작 시

```bash
pkill -f bot.py
pkill -f status_bot.py
nohup python3 bot.py > bot.log 2>&1 &
ps aux | grep status_bot.py
```

## 💡 기타 사항

- 봇이 오프라인으로 보이면 서버가 꺼져있거나 봇 프로세스가 죽은 것입니다.
- 봇은 서버 안에서 실행되므로, **서버가 재시작되면 봇도 수동으로 다시 실행해야 합니다.**
  
  ```bash
  ## xaerinoo 계정의 ~/discord-bot 폴더에서
  pkill -f status_bot.py
  nohup python status_bot.py > bot.log 2>&1 &
  ```
