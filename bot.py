import discord
from discord import app_commands
import psutil
import subprocess
import time
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def get_gpu_info():
    try:
        result = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        gpus = []
        for i, line in enumerate(lines):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 5:
                name, util, mem_used, mem_total, temp = parts
                gpus.append({
                    "index": i,
                    "name": name,
                    "util": int(util),
                    "mem_used": int(mem_used),
                    "mem_total": int(mem_total),
                    "temp": int(temp),
                })
        return gpus
    except Exception as e:
        return None


def get_uptime():
    uptime_seconds = int(time.time() - psutil.boot_time())
    d = uptime_seconds // 86400
    h = (uptime_seconds % 86400) // 3600
    m = (uptime_seconds % 3600) // 60
    return f"{d}일 {h}시간 {m}분"


def make_status_embed():
    embed = discord.Embed(
        title="Monitoring Server Status",
        color=0x00ff99,
        timestamp=discord.utils.utcnow()
    )

    # 서버 켜진 시간
    embed.add_field(name="Uptime", value=get_uptime(), inline=False)

    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_cores = psutil.cpu_count()
    cpu_bar = make_bar(cpu_percent)
    embed.add_field(
        name="CPU",
        value=f"{cpu_bar} **{cpu_percent}%** ({cpu_cores}코어)",
        inline=False
    )

    # RAM
    mem = psutil.virtual_memory()
    mem_bar = make_bar(mem.percent)
    embed.add_field(
        name="RAM",
        value=f"{mem_bar} **{mem.percent}%** ({mem.used // 1024**3:.1f} / {mem.total // 1024**3:.1f} GB)",
        inline=False
    )

    # GPU
    gpus = get_gpu_info()
    if gpus:
        for gpu in gpus:
            gpu_bar = make_bar(gpu["util"])
            mem_bar = make_bar(gpu["mem_used"] / gpu["mem_total"] * 100)
            embed.add_field(
                name=f"GPU {gpu['index']} — {gpu['name']}",
                value=(
                    f"연산: {gpu_bar} **{gpu['util']}%**\n"
                    f"메모리: {mem_bar} **{gpu['mem_used']} / {gpu['mem_total']} MiB**\n"
                    f"온도: **{gpu['temp']}°C**"
                ),
                inline=False
            )
    else:
        embed.add_field(name="GPU", value="정보를 가져올 수 없어요", inline=False)

    embed.set_footer(text="CPSS Lab Server")
    return embed


def make_bar(percent, length=10):
    filled = int(percent / 100 * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"`{bar}`"


@tree.command(name="status", description="서버 상태를 확인합니다")
async def status(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = make_status_embed()
    await interaction.followup.send(embed=embed)


@client.event
async def on_ready():
    await tree.sync()
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="서버 상태 모니터링 중"
        )
    )
    print(f"봇 온라인: {client.user}")


client.run(BOT_TOKEN)