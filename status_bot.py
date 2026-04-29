import discord
from discord import app_commands
import psutil
import subprocess
import time
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not BOT_TOKEN:
    raise RuntimeError("TOKEN is not set in environment")
if not CHANNEL_ID:
    raise RuntimeError("CHANNEL_ID is not set in environment")

CHANNEL_ID = int(CHANNEL_ID)

GPU_THRESHOLD = 30
CHECK_INTERVAL = 30

EXPERIMENT_PROCESSES = [
    "python",
    "python3",
]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

experiment_state = {
    "processes": {}
}

monitor_task = None


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
        print(f"[get_gpu_info error] {e}")
        return None


def get_experiment_processes():
    found = {}
    for proc in psutil.process_iter(["pid", "name", "cmdline", "username"]):
        try:
            name = proc.info["name"] or ""
            cmdline = " ".join(proc.info["cmdline"] or [])
            user = proc.info.get("username", "unknown")

            for keyword in EXPERIMENT_PROCESSES:
                if keyword.lower() in name.lower() or keyword.lower() in cmdline.lower():
                    found[proc.info["pid"]] = {
                        "user": user,
                        "name": name
                    }
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return found


def get_uptime():
    uptime_seconds = int(time.time() - psutil.boot_time())
    d = uptime_seconds // 86400
    h = (uptime_seconds % 86400) // 3600
    m = (uptime_seconds % 3600) // 60
    return f"{d}일 {h}시간 {m}분"


def make_bar(percent, length=10):
    filled = int(percent / 100 * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"`{bar}`"


def add_gpu_fields(embed, gpus):
    if not gpus:
        embed.add_field(name="GPU", value="No info", inline=False)
        return

    for g in gpus:
        gpu_bar = make_bar(g["util"])
        mem_bar = make_bar(g["mem_used"] / g["mem_total"] * 100)

        embed.add_field(
            name=f"GPU {g['index']} — {g['name']}",
            value=(
                f"연산: {gpu_bar} **{g['util']}%**\n"
                f"메모리: {mem_bar} **{g['mem_used']} / {g['mem_total']} MiB**\n"
                f"온도: **{g['temp']}C**"
            ),
            inline=False
        )


def make_status_embed():
    embed = discord.Embed(
        title="Monitoring Server Status",
        color=0x00ff99,
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(name="Uptime", value=get_uptime(), inline=False)

    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_cores = psutil.cpu_count()
    cpu_bar = make_bar(cpu_percent)
    embed.add_field(
        name="CPU",
        value=f"{cpu_bar} **{cpu_percent}%** ({cpu_cores} 코어)",
        inline=False
    )

    mem = psutil.virtual_memory()
    mem_bar = make_bar(mem.percent)
    embed.add_field(
        name="RAM",
        value=f"{mem_bar} **{mem.percent}%** ({mem.used // 1024**3:.1f} / {mem.total // 1024**3:.1f} GB)",
        inline=False
    )

    gpus = get_gpu_info()
    add_gpu_fields(embed, gpus)

    current_procs = get_experiment_processes()
    lines = []
    for pid, info in experiment_state["processes"].items():
        if pid not in current_procs:
            continue

        secs = int(time.time() - info["start_time"])
        h, m = divmod(secs // 60, 60)
        lines.append(f"`PID {pid}` {info['name']} ({info['user']}, {h}시간 {m}분째)")

    embed.add_field(
        name="Experiment",
        value="\n".join(lines) if lines else "-",
        inline=False
    )

    embed.set_footer(text="CPSS Lab Server")
    return embed


async def experiment_monitor():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            gpus = get_gpu_info()
            current_procs = get_experiment_processes()

            current_pids = set(current_procs.keys())
            tracked_pids = set(experiment_state["processes"].keys())

            new_pids = current_pids - tracked_pids
            for pid in new_pids:
                experiment_state["processes"][pid] = {
                    "user": current_procs[pid]["user"],
                    "name": current_procs[pid]["name"],
                    "start_time": time.time()
                }

                embed = discord.Embed(
                    title="🟡 실험이 시작됨",
                    color=0xffff52,
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    value=(
                        f"User: {current_procs[pid]['user']}\n"
                        f"PID: {pid}\n"
                        f"Process: {current_procs[pid]['name']}"
                    ),
                    inline=False
                )
                add_gpu_fields(embed, gpus)
                embed.set_footer(text="CPSS Lab Server")
                await channel.send(embed=embed)

            ended_pids = tracked_pids - current_pids
            for pid in ended_pids:
                info = experiment_state["processes"].pop(pid, None)
                if not info:
                    continue

                duration = int(time.time() - info["start_time"])
                h, m = divmod(duration // 60, 60)

                embed = discord.Embed(
                    title="🟡 실험이 종료됨",
                    color=0xff0000,
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="Info",
                    value=(
                        f"User: {info['user']}\n"
                        f"PID: {pid}\n"
                        f"Process: {info['name']}"
                    ),
                    inline=False
                )
                embed.add_field(
                    name="Duration",
                    value=f"{h}시간 {m}분 동안 진행됨",
                    inline=False
                )
                embed.set_footer(text="CPSS Lab Server")
                await channel.send(embed=embed)

        except Exception as e:
            print(f"[monitor error] {e}")

        await asyncio.sleep(CHECK_INTERVAL)


@tree.command(name="status", description="Check server status")
async def status(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = make_status_embed()
    await interaction.followup.send(embed=embed)


@client.event
async def on_ready():
    global monitor_task

    await tree.sync()
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Monitoring server status"
        )
    )
    print(f"Bot online: {client.user}")

    if monitor_task is None or monitor_task.done():
        monitor_task = asyncio.create_task(experiment_monitor())


client.run(BOT_TOKEN)