# CPSS Server Status Bot

CPSS 연구실 서버 상태를 디스코드에서 확인할 수 있는 봇입니다.  
`/status` 명령어를 입력하면 CPU, RAM, GPU 사용량을 확인할 수 있습니다.

## 파일 구조

```
discord-bot/
├── bot.py        # 디코봇
├── .env
├── .gitignore
└── README.md
```

## 코드 수정 후 재시작 시

```bash
pkill -f bot.py && nohup python3 bot.py > bot.log 2>&1 &
```

## 봇 끄기

```bash
pkill -f bot.py
```

## 봇이 실행 중인지 확인

```bash
pgrep -a python3
```

## 서버가 꺼졌는지 알 수 있는 방법은 없나요?

- 봇이 오프라인(회색)으로 보이면 서버가 꺼져있거나 봇 프로세스가 죽은 것입니다.
- 봇은 서버 안에서 실행되므로, 서버가 재시작되면 봇도 수동으로 다시 실행해야 합니다.