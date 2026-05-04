#!/usr/bin/env python3
"""
Safe Delete Manager v4.0 - Modern TUI
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt, IntPrompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns
except ImportError:
    print("Installing rich...")
    os.system("pip install rich -q")
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt, IntPrompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns

console = Console()

# ─── CONFIG ───────────────────────────────────────────────
TRASH_DIR = Path.home() / ".safe_delete_trash"
LOG_FILE = Path.home() / ".safe_delete_log.json"

# ─── UTILITIES ────────────────────────────────────────────
def ensure_trash():
    TRASH_DIR.mkdir(parents=True, exist_ok=True)

def log_action(action, paths, success=True, details=""):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "paths": [str(p) for p in paths],
        "success": success,
        "details": details
    }
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except:
            pass
    logs.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs[-500:], f, indent=2, ensure_ascii=False)

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def get_path_info(path):
    p = Path(path).expanduser().resolve()
    info = {
        "exists": p.exists(),
        "is_file": p.is_file(),
        "is_dir": p.is_dir(),
        "size": 0,
        "item_count": 0,
        "permissions": oct(p.stat().st_mode)[-3:] if p.exists() else "???",
        "modified": "",
        "path": str(p)
    }
    if p.exists():
        try:
            stat = p.stat()
            info["modified"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            if p.is_file():
                info["size"] = stat.st_size
            elif p.is_dir():
                count = 0
                total_size = 0
                for item in p.rglob("*"):
                    count += 1
                    try:
                        if item.is_file():
                            total_size += item.stat().st_size
                    except:
                        pass
                info["item_count"] = count
                info["size"] = total_size
        except Exception as e:
            info["error"] = str(e)
    return info

def safe_delete(paths, move_to_trash=True, dry_run=False):
    results = []
    ensure_trash()

    with Progress(
        SpinnerColumn("dots", style="bright_green"),
        TextColumn("[bold white]{task.description}[/bold white]"),
        console=console,
        transient=True
    ) as progress:
        for path_str in paths:
            p = Path(path_str).expanduser().resolve()
            task = progress.add_task(f"Menghapus {p.name}...", total=None)

            if not p.exists():
                results.append((str(p), False, "Path tidak ditemukan"))
                progress.update(task, completed=True)
                continue

            if dry_run:
                results.append((str(p), True, "DRY RUN - tidak dihapus"))
                progress.update(task, completed=True)
                continue

            try:
                if move_to_trash:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    trash_name = f"{timestamp}_{p.name}"
                    trash_path = TRASH_DIR / trash_name

                    if p.is_file():
                        shutil.copy2(p, trash_path)
                        p.unlink()
                    elif p.is_dir():
                        shutil.copytree(p, trash_path)
                        shutil.rmtree(p)

                    results.append((str(p), True, f"Dipindahkan ke trash"))
                    log_action("move_to_trash", [p, trash_path], True)
                else:
                    if p.is_file():
                        p.unlink()
                    elif p.is_dir():
                        shutil.rmtree(p)

                    results.append((str(p), True, "Dihapus permanen"))
                    log_action("permanent_delete", [p], True)

            except Exception as e:
                results.append((str(p), False, str(e)))
                log_action("delete_failed", [p], False, str(e))

            progress.update(task, completed=True)

    return results

def list_trash():
    if not TRASH_DIR.exists():
        return []
    items = []
    for item in TRASH_DIR.iterdir():
        try:
            stat = item.stat()
            size = 0
            if item.is_file():
                size = stat.st_size
            elif item.is_dir():
                for f in item.rglob("*"):
                    if f.is_file():
                        size += f.stat().st_size
            items.append({
                "name": item.name,
                "path": item,
                "size": size,
                "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            })
        except:
            pass
    return sorted(items, key=lambda x: x["date"], reverse=True)

# ─── BROWSER ──────────────────────────────────────────────
def browse_directory(start_path="."):
    current_path = Path(start_path).expanduser().resolve()
    selected_items = []

    while True:
        console.clear()
        header = f"[bold bright_cyan]📂 {current_path}[/bold bright_cyan]"
        sub = "[dim]nomor=pilih | d [nomor]=masuk | b=kembali | a=semua | x=selesai | q=batal[/dim]"
        console.print(Panel(
            Align.center(header + "\n" + sub),
            style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2)
        ))

        try:
            items = []
            if current_path != current_path.parent:
                items.append({"type": "parent", "path": current_path.parent, "name": "📁 .."})

            all_entries = list(current_path.iterdir())
            dirs = sorted([p for p in all_entries if p.is_dir()], key=lambda x: x.name.lower())
            files = sorted([p for p in all_entries if p.is_file()], key=lambda x: x.name.lower())

            for d in dirs:
                items.append({"type": "dir", "path": d, "name": f"📁 {d.name}/"})
            for f in files:
                size = format_size(f.stat().st_size) if f.exists() else "???"
                items.append({"type": "file", "path": f, "name": f"📄 {f.name}", "size": size})

        except PermissionError:
            console.print(Panel("[red]🔒 Permission denied[/red]", box=box.ROUNDED))
            input("\nTekan Enter...")
            current_path = current_path.parent
            continue
        except Exception as e:
            console.print(Panel(f"[red]❌ Error: {e}[/red]", box=box.ROUNDED))
            input("\nTekan Enter...")
            break

        if not items:
            console.print(Panel("[dim]📂 Folder kosong[/dim]", box=box.ROUNDED, style="dim"))
        else:
            table = Table(
                show_header=True,
                box=box.ROUNDED,
                border_style="bright_black",
                header_style="bold bright_white",
                row_styles=["", "dim"]
            )
            table.add_column("No", style="bold bright_yellow", width=5, justify="center")
            table.add_column("Nama", style="bold bright_white")
            table.add_column("Tipe", width=10, style="bright_magenta")
            table.add_column("Ukuran", justify="right", width=12, style="bright_green")
            table.add_column("Modified", style="dim", width=16)

            for i, item in enumerate(items, 1):
                path = item["path"]
                name = item["name"]
                item_type = "Folder" if item["type"] in ["dir", "parent"] else "File"
                size = item.get("size", "-") if item["type"] == "file" else "-"

                marker = ""
                if str(path) in [str(s) for s in selected_items]:
                    marker = " [bright_green]✓[/bright_green]"

                try:
                    mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d %H:%M")
                except:
                    mtime = "???"

                table.add_row(str(i), name + marker, item_type, size, mtime)

            console.print(table)

        if selected_items:
            sel_text = f"[bright_green]📌 {len(selected_items)} item dipilih[/bright_green]"
            console.print(Panel(sel_text, box=box.ROUNDED, style="green", padding=(0, 2)))

        console.print("\n[dim]Command:[/dim] [bold bright_white]nomor[/bold bright_white] | [bold bright_white]d [nomor][/bold bright_white] | [bold bright_white]b[/bold bright_white] | [bold bright_white]a[/bold bright_white] | [bold bright_white]x[/bold bright_white] | [bold bright_white]q[/bold bright_white]")
        choice = Prompt.ask("[bold bright_cyan]▶[/bold bright_cyan]", default="").strip()

        if choice.lower() == "q":
            return []

        if choice.lower() == "x":
            break

        if choice.lower() == "b":
            if current_path != current_path.parent:
                current_path = current_path.parent
            continue

        if choice.lower() == "a":
            for item in items:
                if item["type"] != "parent" and str(item["path"]) not in [str(s) for s in selected_items]:
                    selected_items.append(item["path"])
            console.print("[bright_green]✅ Semua item dipilih[/bright_green]")
            input("Tekan Enter...")
            continue

        if choice.lower().startswith("d "):
            try:
                idx = int(choice.split()[1]) - 1
                if 0 <= idx < len(items) and items[idx]["type"] in ["dir", "parent"]:
                    current_path = items[idx]["path"]
                else:
                    console.print("[red]❌ Bukan folder[/red]")
                    input("Tekan Enter...")
            except:
                console.print("[red]❌ Format: d [nomor][/red]")
                input("Tekan Enter...")
            continue

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                selected_path = items[idx]["path"]

                if str(selected_path) in [str(s) for s in selected_items]:
                    selected_items = [s for s in selected_items if str(s) != str(selected_path)]
                    console.print(f"[bright_yellow]✗ Dibatalkan: {selected_path.name}[/bright_yellow]")
                else:
                    selected_items.append(selected_path)
                    console.print(f"[bright_green]✓ Dipilih: {selected_path.name}[/bright_green]")

                input("Tekan Enter...")
            else:
                console.print("[red]❌ Nomor tidak valid[/red]")
                input("Tekan Enter...")
        except ValueError:
            if choice:
                console.print("[red]❌ Input tidak valid[/red]")
                input("Tekan Enter...")

    return selected_items

def select_items_glob():
    console.clear()
    header = "[bold bright_cyan]🔍 PILIH DENGAN PATTERN[/bold bright_cyan]"
    sub = "[dim]Wildcard: *.txt, *.py, folder/*, dll[/dim]"
    console.print(Panel(
        Align.center(header + "\n" + sub),
        style="bright_blue",
        box=box.ROUNDED,
        padding=(1, 2)
    ))

    pattern = Prompt.ask("[bold bright_white]📁 Pattern[/bold bright_white]", default="*")
    start_path = Prompt.ask("[bold bright_white]📂 Direktori[/bold bright_white]", default=".")

    p = Path(start_path).expanduser()
    if not p.exists():
        console.print(Panel("[red]❌ Direktori tidak ditemukan[/red]", box=box.ROUNDED))
        input("Tekan Enter...")
        return []

    matches = list(p.glob(pattern))
    if not matches:
        console.print(Panel(f"[yellow]⚠️ Tidak ada hasil untuk '{pattern}'[/yellow]", box=box.ROUNDED))
        input("Tekan Enter...")
        return []

    dirs = sorted([m for m in matches if m.is_dir()], key=lambda x: x.name.lower())
    files = sorted([m for m in matches if m.is_file()], key=lambda x: x.name.lower())
    matches = dirs + files

    selected = []
    while True:
        console.clear()
        header2 = f"[bold bright_cyan]📋 HASIL: {pattern}[/bold bright_cyan]"
        sub2 = f"[dim]{len(matches)} item di {p}[/dim]"
        console.print(Panel(
            Align.center(header2 + "\n" + sub2),
            style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2)
        ))

        table = Table(
            show_header=True,
            box=box.ROUNDED,
            border_style="bright_black",
            header_style="bold bright_white",
            row_styles=["", "dim"]
        )
        table.add_column("No", style="bold bright_yellow", width=5, justify="center")
        table.add_column("Nama", style="bold bright_white")
        table.add_column("Tipe", width=10, style="bright_magenta")
        table.add_column("Ukuran", justify="right", width=12, style="bright_green")
        table.add_column("Path", style="dim")

        for i, m in enumerate(matches, 1):
            name = m.name
            item_type = "Folder" if m.is_dir() else "File"
            size = format_size(m.stat().st_size) if m.is_file() and m.exists() else "-"
            path_str = str(m.parent)[:30]

            marker = ""
            if str(m) in [str(s) for s in selected]:
                marker = " [bright_green]✓[/bright_green]"

            table.add_row(str(i), name + marker, item_type, size, path_str)

        console.print(table)

        if selected:
            sel_text = f"[bright_green]📌 {len(selected)} item dipilih[/bright_green]"
            console.print(Panel(sel_text, box=box.ROUNDED, style="green", padding=(0, 2)))

        console.print("\n[dim]Command:[/dim] [bold bright_white]nomor[/bold bright_white] | [bold bright_white]a[/bold bright_white] | [bold bright_white]x[/bold bright_white] | [bold bright_white]q[/bold bright_white]")
        choice = Prompt.ask("[bold bright_cyan]▶[/bold bright_cyan]", default="").strip()

        if choice.lower() == "q":
            return []

        if choice.lower() == "x":
            break

        if choice.lower() == "a":
            selected = matches.copy()
            console.print("[bright_green]✅ Semua item dipilih[/bright_green]")
            input("Tekan Enter...")
            continue

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(matches):
                path = matches[idx]
                if str(path) in [str(s) for s in selected]:
                    selected = [s for s in selected if str(s) != str(path)]
                    console.print(f"[bright_yellow]✗ Dibatalkan: {path.name}[/bright_yellow]")
                else:
                    selected.append(path)
                    console.print(f"[bright_green]✓ Dipilih: {path.name}[/bright_green]")
                input("Tekan Enter...")
            else:
                console.print("[red]❌ Nomor tidak valid[/red]")
                input("Tekan Enter...")
        except ValueError:
            if choice:
                console.print("[red]❌ Input tidak valid[/red]")
                input("Tekan Enter...")

    return selected

# ─── DELETE WORKFLOW ──────────────────────────────────────
def execute_delete(selected_paths):
    if not selected_paths:
        console.print(Panel("[yellow]⚠️ Tidak ada item yang dipilih[/yellow]", box=box.ROUNDED))
        return

    console.clear()
    console.print(Panel(
        "[bold bright_red]📋 RINGKASAN ITEM YANG AKAN DIHAPUS[/bold bright_red]",
        style="bright_red",
        box=box.ROUNDED,
        padding=(1, 2)
    ))

    table = Table(
        show_header=True,
        box=box.ROUNDED,
        border_style="bright_black",
        header_style="bold bright_white",
        row_styles=["", "dim"]
    )
    table.add_column("No", style="bold bright_yellow", width=4, justify="center")
    table.add_column("Nama", style="bold bright_cyan")
    table.add_column("Tipe", width=10, style="bright_magenta")
    table.add_column("Ukuran", justify="right", width=12, style="bright_green")
    table.add_column("Path", style="dim")

    total_size = 0
    for i, path in enumerate(selected_paths, 1):
        info = get_path_info(path)
        total_size += info["size"]
        table.add_row(
            str(i),
            path.name,
            "File" if info["is_file"] else "Folder",
            format_size(info["size"]),
            str(path)[:45]
        )

    table.add_row("", "[bold bright_white]TOTAL", "", f"[bold bright_green]{format_size(total_size)}[/bold bright_green]", "", style="bold")
    console.print(table)

    console.print("\n[bold bright_white]Opsi Penghapusan:[/bold bright_white]")
    opts = [
        "[bold bright_green]1[/bold bright_green]  🗑️  Pindahkan ke Trash",
        "[bold bright_red]2[/bold bright_red]  💥 Hapus Permanen",
        "[bold bright_yellow]3[/bold bright_yellow]  🧪 Dry Run",
        "[bold bright_black]0[/bold bright_black]  ❌ Batal"
    ]
    console.print(Columns(opts, equal=True))

    choice = IntPrompt.ask("[bold bright_cyan]Pilih opsi[/bold bright_cyan]", default=1)

    if choice == 0:
        console.print("[bright_yellow]❌ Dibatalkan[/bright_yellow]")
        return

    move_to_trash = (choice == 1)
    dry_run = (choice == 3)

    if dry_run:
        console.print("\n[bright_yellow]🧪 DRY RUN MODE[/bright_yellow]")

    if not dry_run:
        if not Confirm.ask(f"\n[bold bright_red]⚠️ Yakin hapus {len(selected_paths)} item?[/bold bright_red]", default=False):
            console.print("[bright_yellow]❌ Dibatalkan[/bright_yellow]")
            return

    results = safe_delete(selected_paths, move_to_trash=move_to_trash, dry_run=dry_run)

    console.print("\n[bold bright_white]📊 Hasil:[/bold bright_white]")
    for path, success, msg in results:
        icon = "✅" if success else "❌"
        color = "bright_green" if success else "bright_red"
        console.print(f"[{color}]{icon} {Path(path).name}: {msg}[/{color}]")

# ─── MENUS ────────────────────────────────────────────────
def show_banner():
    banner = "🗑️  [bold bright_red]SAFE DELETE MANAGER[/bold bright_red]  [dim]v4.0[/dim]"
    console.print(Panel(
        Align.center(banner),
        style="bright_red",
        box=box.ROUNDED,
        padding=(1, 4)
    ))

def show_menu():
    menu_data = [
        ("1", "📂 Browse Folder", "Pilih file/folder dengan nomor", "bright_green"),
        ("2", "🔍 Cari Pattern", "Wildcard: *.txt, *.py, dll", "bright_yellow"),
        ("3", "📝 Path Manual", "Ketik path langsung", "bright_cyan"),
        ("4", "🧹 Kosongkan Trash", "Hapus semua isi trash", "bright_red"),
        ("5", "📋 Lihat Trash", "Cek isi trash", "bright_blue"),
        ("6", "📝 Log Aktivitas", "Riwayat penghapusan", "bright_magenta"),
        ("7", "🔧 Settings", "Atur konfigurasi", "bright_white"),
        ("0", "❌ Keluar", "Tutup aplikasi", "bright_black"),
    ]

    table = Table(
        show_header=False,
        box=box.ROUNDED,
        border_style="bright_black",
        padding=(0, 1)
    )
    table.add_column("No", style="bold", width=5, justify="center")
    table.add_column("Menu", style="bold", width=22)
    table.add_column("Deskripsi", style="dim")

    for num, menu, desc, color in menu_data:
        table.add_row(
            f"[{color}]{num}[/{color}]",
            f"[{color}]{menu}[/{color}]",
            desc
        )

    console.print(table)

def menu_browse():
    start_path = Prompt.ask("[bold bright_white]📁 Mulai dari direktori[/bold bright_white]", default=".")
    selected = browse_directory(start_path)
    if selected:
        execute_delete(selected)

def menu_pattern():
    selected = select_items_glob()
    if selected:
        execute_delete(selected)

def menu_manual():
    console.print(Panel(
        "[bold bright_cyan]📝 Mode Manual[/bold bright_cyan]\n[dim]Masukkan path satu per satu. Ketik 'done' untuk selesai.[/dim]",
        box=box.ROUNDED,
        style="bright_cyan",
        padding=(1, 2)
    ))

    paths = []
    while True:
        path_input = Prompt.ask("[bold bright_white]📁 Path[/bold bright_white]", default="done")
        if path_input.lower() in ["done", "exit", "q"]:
            break

        p = Path(path_input).expanduser()
        if not p.exists():
            console.print(f"[bright_red]❌ Tidak ditemukan: {p}[/bright_red]")
            continue

        paths.append(str(p))
        console.print(f"[bright_green]✓ {p.name}[/bright_green]")

    if paths:
        execute_delete([Path(p) for p in paths])

def menu_empty_trash():
    items = list_trash()

    if not items:
        console.print(Panel("[bright_yellow]🗑️ Trash kosong[/bright_yellow]", box=box.ROUNDED))
        return

    total_size = sum(item["size"] for item in items)

    console.print(Panel(
        f"[bold bright_red]🗑️ Trash ({len(items)} item, {format_size(total_size)})[/bold bright_red]",
        box=box.ROUNDED,
        style="bright_red",
        padding=(1, 2)
    ))

    table = Table(
        show_header=True,
        box=box.ROUNDED,
        border_style="bright_black",
        header_style="bold bright_white",
        row_styles=["", "dim"]
    )
    table.add_column("No", style="bold bright_yellow", width=4, justify="center")
    table.add_column("Nama", style="bright_cyan")
    table.add_column("Ukuran", justify="right", width=12, style="bright_green")
    table.add_column("Tanggal", style="dim", width=16)

    for i, item in enumerate(items, 1):
        table.add_row(str(i), item["name"], format_size(item["size"]), item["date"])

    console.print(table)

    if Confirm.ask(f"\n[bold bright_red]⚠️ Hapus semua {len(items)} item?[/bold bright_red]", default=False):
        deleted = 0
        failed = 0
        for item in items:
            try:
                p = item["path"]
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    shutil.rmtree(p)
                deleted += 1
            except Exception as e:
                console.print(f"[bright_red]❌ Gagal: {item['name']} - {e}[/bright_red]")
                failed += 1

        if deleted > 0:
            console.print(f"[bright_green]✅ {deleted} item dihapus[/bright_green]")
        if failed > 0:
            console.print(f"[bright_red]❌ {failed} item gagal[/bright_red]")

def menu_view_trash():
    items = list_trash()

    if not items:
        console.print(Panel("[bright_yellow]🗑️ Trash kosong[/bright_yellow]", box=box.ROUNDED))
        return

    total_size = sum(item["size"] for item in items)

    console.print(Panel(
        f"[bold bright_blue]📋 Trash ({len(items)} item, {format_size(total_size)})[/bold bright_blue]",
        box=box.ROUNDED,
        style="bright_blue",
        padding=(1, 2)
    ))

    table = Table(
        show_header=True,
        box=box.ROUNDED,
        border_style="bright_black",
        header_style="bold bright_white",
        row_styles=["", "dim"]
    )
    table.add_column("No", style="bold bright_yellow", width=4, justify="center")
    table.add_column("Nama", style="bright_cyan")
    table.add_column("Ukuran", justify="right", width=12, style="bright_green")
    table.add_column("Tanggal", style="dim", width=16)
    table.add_column("Path", style="dim")

    for i, item in enumerate(items, 1):
        table.add_row(
            str(i),
            item["name"],
            format_size(item["size"]),
            item["date"],
            str(item["path"])[:35]
        )

    console.print(table)
    console.print(f"\n[dim]📍 {TRASH_DIR}[/dim]")

def menu_view_logs():
    if not LOG_FILE.exists():
        console.print(Panel("[bright_yellow]📝 Belum ada log[/bright_yellow]", box=box.ROUNDED))
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except:
        console.print(Panel("[bright_red]❌ Gagal membaca log[/bright_red]", box=box.ROUNDED))
        return

    if not logs:
        console.print(Panel("[bright_yellow]📝 Log kosong[/bright_yellow]", box=box.ROUNDED))
        return

    console.print(Panel(
        f"[bold bright_magenta]📝 Log Aktivitas ({len(logs)} entri)[/bold bright_magenta]",
        box=box.ROUNDED,
        style="bright_magenta",
        padding=(1, 2)
    ))

    table = Table(
        show_header=True,
        box=box.ROUNDED,
        border_style="bright_black",
        header_style="bold bright_white",
        row_styles=["", "dim"]
    )
    table.add_column("Waktu", style="dim", width=18)
    table.add_column("Aksi", width=18, style="bright_cyan")
    table.add_column("Status", width=8, justify="center")
    table.add_column("Detail", style="bright_white")

    for log in logs[-50:]:
        status = "✅" if log.get("success") else "❌"
        color = "bright_green" if log.get("success") else "bright_red"
        paths = ", ".join(log.get("paths", [])[:2])
        detail = log.get("details", paths)
        table.add_row(
            log.get("timestamp", "")[:16],
            log.get("action", ""),
            f"[{color}]{status}[/{color}]",
            detail[:50]
        )

    console.print(table)

def menu_settings():
    global TRASH_DIR

    console.print(Panel(
        "[bold bright_white]🔧 Settings[/bold bright_white]",
        box=box.ROUNDED,
        style="bright_white",
        padding=(1, 2)
    ))

    console.print(f"\n[dim]Current:[/dim]")
    console.print(f"  🗑️  Trash: [bright_cyan]{TRASH_DIR}[/bright_cyan]")
    console.print(f"  📝 Log: [bright_cyan]{LOG_FILE}[/bright_cyan]")

    console.print("\n[bold bright_white]Opsi:[/bold bright_white]")
    opts = [
        "[bold bright_green]1[/bold bright_green]  Ganti Trash Directory",
        "[bold bright_red]2[/bold bright_red]  Hapus Semua Log",
        "[bold bright_black]0[/bold bright_black]  Kembali"
    ]
    console.print(Columns(opts, equal=True))

    choice = IntPrompt.ask("[bold bright_cyan]Pilih[/bold bright_cyan]", default=0)

    if choice == 1:
        new_path = Prompt.ask("[bold bright_white]Path trash baru[/bold bright_white]", default=str(TRASH_DIR))
        TRASH_DIR = Path(new_path).expanduser()
        ensure_trash()
        console.print(f"[bright_green]✅ Trash: {TRASH_DIR}[/bright_green]")
    elif choice == 2:
        if LOG_FILE.exists() and Confirm.ask("[bold bright_red]Hapus semua log?[/bold bright_red]", default=False):
            LOG_FILE.unlink()
            console.print("[bright_green]✅ Log dihapus[/bright_green]")

# ─── MAIN ─────────────────────────────────────────────────
def main():
    try:
        while True:
            console.clear()
            show_banner()
            show_menu()

            choice = IntPrompt.ask("\n[bold bright_cyan]Pilih menu[/bold bright_cyan]", default=0)

            if choice == 1:
                menu_browse()
            elif choice == 2:
                menu_pattern()
            elif choice == 3:
                menu_manual()
            elif choice == 4:
                menu_empty_trash()
            elif choice == 5:
                menu_view_trash()
            elif choice == 6:
                menu_view_logs()
            elif choice == 7:
                menu_settings()
            elif choice == 0:
                console.print("\n[bright_green]👋 Sampai jumpa![/bright_green]")
                break
            else:
                console.print("[bright_red]❌ Pilihan tidak valid[/bright_red]")

            if choice != 0:
                console.print("\n[dim]Tekan Enter untuk kembali...[/dim]")
                input()

    except KeyboardInterrupt:
        console.print("\n\n[bright_yellow]⚠️ Interrupted[/bright_yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bright_red]❌ Error: {e}[/bright_red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
