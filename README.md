# ⚡ LuaBoost Localizer v1.0.0

**Automatic global-to-local optimizer for World of Warcraft 3.3.5a addon Lua files.**

In Lua 5.1, accessing global variables (`GetTime`, `math.floor`, `UnitHealth`, etc.) requires a slow hash table lookup on every call. Caching them as `local` references speeds up execution by **10-30%** for hot-path code.

Most addon authors don't bother doing this for every function. This tool does it automatically for all your addons — without modifying their logic.

Part of the **[LuaBoost](https://github.com/suprepupre/LuaBoost)** optimization ecosystem.

---

## 🚀 Quick Start

### Option A: Standalone EXE (no Python needed)

1. Download `luaboost_localizer.exe` from [Releases](../../releases/latest)
2. Place it anywhere
3. Run:

```bash
# Preview what would change (safe, no modifications):
luaboost_localizer.exe "C:\WoW 3.3.5a\Interface\AddOns" --dry-run

# Apply optimizations:
luaboost_localizer.exe "C:\WoW 3.3.5a\Interface\AddOns"

# Undo everything:
luaboost_localizer.exe "C:\WoW 3.3.5a\Interface\AddOns" --undo
```

### Option B: Python script

```bash
python luaboost_localizer.py "C:\WoW 3.3.5a\Interface\AddOns" --dry-run
```

---

## ✅ What It Does

### Before (addon code):
```lua
function MyAddon:OnUpdate()
    local hp = UnitHealth("target")
    local maxHp = UnitHealthMax("target")
    local pct = math.floor(hp / maxHp * 100)
    local name = UnitName("target")
    self.text:SetText(string.format("%s: %d%%", name, pct))
end
```

### After:
```lua
-- [LuaBoost Localizer] Auto-generated local references
-- math
local math_floor = math.floor
-- string
local string_format = string.format
-- WoW API
local UnitHealth = UnitHealth
local UnitHealthMax = UnitHealthMax
local UnitName = UnitName
-- [/LuaBoost Localizer]

function MyAddon:OnUpdate()
    local hp = UnitHealth("target")
    local maxHp = UnitHealthMax("target")
    local pct = math_floor(hp / maxHp * 100)
    local name = UnitName("target")
    self.text:SetText(string_format("%s: %d%%", name, pct))
end
```

**Key changes:**
- `math.floor()` → `math_floor()` (dotted lookup eliminated)
- `string.format()` → `string_format()` (dotted lookup eliminated)
- `UnitHealth` etc. → cached as local (global lookup eliminated)
- Original logic is **completely unchanged**

---

## 🛡️ Safety

| Feature | How It Works |
|---------|-------------|
| **Tokenizer-based parser** | Full Lua tokenizer separates code from strings/comments. Never modifies string content or comments. |
| **Long string support** | Correctly handles `[[...]]` and `[=[...]=]` at any nesting level |
| **Method calls preserved** | `:method()` calls are never touched — regex excludes `:` prefix |
| **Existing locals detected** | Scans for existing `local X = X` patterns and skips them |
| **Minimum usage threshold** | Only localizes globals used 2+ times (configurable) |
| **Libs/ excluded** | Library folders are automatically skipped |
| **Locale files excluded** | Localization files (enUS.lua, koKR.lua, etc.) are skipped |
| **Backup system** | Creates `.lua.bak` before every modification |
| **Full undo** | `--undo` restores all files from backups |
| **Dry run** | `--dry-run` previews all changes without touching files |

---

## 📊 Global Catalog

The tool knows about **150+ globals** across three categories:

### Lua Standard Library (~50)
`math.floor`, `math.ceil`, `math.abs`, `math.min`, `math.max`, `math.random`, `math.huge`,
`string.format`, `string.find`, `string.match`, `string.gsub`, `string.sub`, `string.lower`,
`table.insert`, `table.remove`, `table.sort`, `table.concat`,
`bit.band`, `bit.bor`, `bit.bxor`,
`pairs`, `ipairs`, `next`, `type`, `tonumber`, `tostring`, `select`, `unpack`,
`pcall`, `xpcall`, `setmetatable`, `getmetatable`, `rawset`, `rawget`,
`date`, `time`, `format`, `wipe`, `tinsert`, `tremove`, `strsplit`, `strmatch`...

### WoW API (~100)
`GetTime`, `UnitHealth`, `UnitHealthMax`, `UnitName`, `UnitGUID`, `UnitClass`,
`UnitExists`, `UnitIsDead`, `UnitAffectingCombat`, `UnitBuff`, `UnitDebuff`,
`GetSpellInfo`, `GetSpellCooldown`, `IsInRaid`, `IsInGroup`, `GetNumGroupMembers`,
`InCombatLockdown`, `CreateFrame`, `GetInstanceInfo`, `IsInInstance`,
`SendAddonMessage`, `SendChatMessage`, `PlaySoundFile`, `GetLocale`...

---

## 🧰 All Commands

| Command | Description |
|---------|-------------|
| `--dry-run` | Preview changes without modifying any files |
| `--report-only` | Show statistics only, no modifications |
| `--verbose` or `-v` | Show detailed per-file and per-global output |
| `--min-uses N` | Minimum uses before localizing (default: 2) |
| `--no-replace` | Only inject local declarations, don't replace dotted calls |
| `--exclude A,B,C` | Skip specific addon folders |
| `--undo` | Restore all files from `.lua.bak` backups |
| `--help` | Show help message |

### Examples

```bash
# Preview everything
luaboost_localizer.exe "C:\WoW\Interface\AddOns" --dry-run -v

# Apply to all addons except LuaBoost and Blizzard UI
luaboost_localizer.exe "C:\WoW\Interface\AddOns" --exclude "!LuaBoost,Blizzard_AuctionUI"

# Only optimize globals used 3+ times
luaboost_localizer.exe "C:\WoW\Interface\AddOns" --min-uses 3

# Only inject locals, don't rename math.floor to math_floor
luaboost_localizer.exe "C:\WoW\Interface\AddOns" --no-replace

# Undo all changes
luaboost_localizer.exe "C:\WoW\Interface\AddOns" --undo

# Process a single addon
luaboost_localizer.exe "C:\WoW\Interface\AddOns\Recount"
```

---

## 📈 Expected Performance Impact

| Scenario | Improvement |
|----------|-------------|
| Dalaran with 50+ players | +2-5 FPS, fewer micro-stutters |
| 25-man ICC raid | +1-3 FPS, smoother frametime |
| Heavy addon setup (10+ addons) | Most noticeable improvement |
| Light addon setup (2-3 addons) | Minimal difference |

The main benefit is **reduced frametime variance** (fewer micro-stutters), not raw FPS increase. Each `GETGLOBAL` opcode saved eliminates a hash table lookup — multiply by thousands of calls per frame across all addons.

---

## 🔧 Building from Source

### Requirements
- Python 3.8+
- PyInstaller (for .exe)

### Build EXE
```bash
pip install pyinstaller
pyinstaller --onefile --name "luaboost_localizer" luaboost_localizer.py
```

Or use the included `build.bat`.

---

## 🔧 Recommended Optimization Stack

| Layer | Tool | What It Does |
|-------|------|--------------|
| **C / Engine** | [wow_optimize.dll](https://github.com/suprepupre/wow-optimize) | Memory allocator, I/O, network, Lua VM, combat log |
| **Lua / Runtime** | [!LuaBoost](https://github.com/suprepupre/LuaBoost) | Smart GC, SpeedyLoad, UI Thrashing Protection |
| **Lua / Source** | **LuaBoost Localizer** | Global-to-local optimization for all addons |

---

## ⚠️ Notes

- **Always test after applying.** While the tool is designed to be safe, some addons may use unusual Lua patterns.
- **Backups are created automatically.** Use `--undo` to restore.
- **Re-running is safe.** The tool detects its own `[LuaBoost Localizer]` marker and skips already-processed files.
- **Addon updates will overwrite changes.** Re-run the tool after updating addons.
- **Libs/ folders are never touched.** Shared libraries should not be modified.

---

## 📜 License

MIT License — do whatever you want with it.