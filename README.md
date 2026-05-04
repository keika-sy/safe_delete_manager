# 🗑️ Safe Delete Manager

> A modern, interactive TUI tool for safely deleting files and folders with numbered selection, trash recovery, and activity logging.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Rich](https://img.shields.io/badge/Rich-TUI-green?style=flat-square)](https://github.com/Textualize/rich)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📂 **Browse & Select** | Navigate folders and select files/folders by number |
| 🔍 **Pattern Search** | Use wildcards (`*.txt`, `*.py`, `folder/*`) to find and select items |
| 🗑️ **Trash System** | Move to trash before permanent deletion — recoverable |
| 🧪 **Dry Run Mode** | Simulate deletion without actually removing anything |
| 📝 **Activity Log** | All actions logged to `~/.safe_delete_log.json` |
| 🎨 **Modern TUI** | Beautiful terminal UI powered by [Rich](https://github.com/Textualize/rich) with rounded boxes |
| ⚡ **Spinner Animation** | Animated progress indicators during operations |
| 🔒 **Safety First** | Double confirmation for permanent deletion |

---

## 📸 Preview

```
╭────────────────────────────────────╮
│  🗑️  SAFE DELETE MANAGER  v4.0    │
╰────────────────────────────────────╯

╭────────────────────────────────────────╮
│  1  📂 Browse Folder      Pilih ...   │
│  2  🔍 Cari Pattern       Wildcard... │
│  3  📝 Path Manual        Ketik ...   │
│  4  🧹 Kosongkan Trash    Hapus ...   │
│  5  📋 Lihat Trash        Cek ...     │
│  6  📝 Log Aktivitas      Riwayat...  │
│  7  🔧 Settings           Atur ...    │
│  0  ❌ Keluar             Tutup ...   │
╰────────────────────────────────────────╯
```

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- `pip` package manager

### Install

```bash
# Clone the repository
git clone https://github.com/keika-sy/safe_delete_manager.git
cd safe_delete_manager

# Install dependency
pip install rich

# Run
python safe_delete_manager.py
```

---

## 📖 Usage

### Menu Options

| # | Menu | Description |
|---|------|-------------|
| **1** | 📂 Browse Folder | Navigate directories and select items by number |
| **2** | 🔍 Cari Pattern | Search with wildcards (e.g., `*.log`, `temp*`) |
| **3** | 📝 Path Manual | Type paths directly (one per line) |
| **4** | 🧹 Kosongkan Trash | Permanently delete all items in trash |
| **5** | 📋 Lihat Trash | View trash contents with size and date |
| **6** | 📝 Log Aktivitas | View last 500 deletion history entries |
| **7** | 🔧 Settings | Change trash directory or clear logs |
| **0** | ❌ Keluar | Exit the application |

### Browser Commands

| Command | Action |
|---------|--------|
| `1`, `2`, `3`... | Select/deselect item by number |
| `d 3` | Enter folder #3 |
| `b` | Go back to parent directory |
| `a` | Select all items in current folder |
| `x` | Finish selection and proceed to delete |
| `q` | Cancel and quit |

### Delete Options

| Option | Description |
|--------|-------------|
| 🗑️ Move to Trash | Safe deletion — items stored in `~/.safe_delete_trash/` |
| 💥 Permanent Delete | Irreversible removal with double confirmation |
| 🧪 Dry Run | Simulation only — nothing actually deleted |

---

## ⚙️ Configuration

### Default Paths

| Setting | Default Path |
|---------|-------------|
| Trash Directory | `~/.safe_delete_trash/` |
| Log File | `~/.safe_delete_log.json` |

### Change Trash Directory
1. Go to **Settings** (menu 7)
2. Select **Change Trash Directory**
3. Enter new path

---

## 🛡️ Safety Features

- **Trash Recovery**: Deleted items are copied to trash before removal
- **Double Confirmation**: Permanent deletion requires explicit confirmation
- **Dry Run**: Test deletions without any risk
- **Activity Logging**: Full audit trail of all operations
- **Permission Checks**: Graceful handling of permission errors

---

## 📝 Log Format

Logs are stored in JSON format:

```json
{
  "timestamp": "2026-05-04T11:25:00",
  "action": "move_to_trash",
  "paths": ["/home/user/file.txt", "~/.safe_delete_trash/20260504_112500_file.txt"],
  "success": true,
  "details": ""
}
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🙏 Acknowledgments

- [Rich](https://github.com/Textualize/rich) — Beautiful terminal formatting
- Inspired by the need for safer file deletion workflows

---

<p align="center">
  Made with ❤️ for safer file management
</p>
