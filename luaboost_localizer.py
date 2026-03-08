import os
import sys
import re
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import defaultdict

__version__ = "1.0.1 (GUI)"

# ============================================================
# WoW API + Lua stdlib global catalog
# ============================================================
LUA_STDLIB = {
    "math.floor": "math_floor", "math.ceil": "math_ceil", "math.abs": "math_abs",
    "math.min": "math_min", "math.max": "math_max", "math.sqrt": "math_sqrt",
    "math.sin": "math_sin", "math.cos": "math_cos", "math.random": "math_random",
    "math.huge": "math_huge", "math.pi": "math_pi", "math.fmod": "math_fmod",
    "math.log": "math_log", "math.pow": "math_pow",
    "string.format": "string_format", "string.find": "string_find",
    "string.match": "string_match", "string.gmatch": "string_gmatch",
    "string.gsub": "string_gsub", "string.sub": "string_sub",
    "string.len": "string_len", "string.byte": "string_byte",
    "string.char": "string_char", "string.rep": "string_rep",
    "string.reverse": "string_reverse", "string.lower": "string_lower",
    "string.upper": "string_upper", "string.split": "string_split",
    "table.insert": "table_insert", "table.remove": "table_remove",
    "table.sort": "table_sort", "table.concat": "table_concat",
    "table.wipe": "table_wipe", "table.getn": "table_getn",
    "bit.band": "bit_band", "bit.bor": "bit_bor", "bit.bxor": "bit_bxor",
    "bit.bnot": "bit_bnot", "bit.lshift": "bit_lshift", "bit.rshift": "bit_rshift",
}

LUA_GLOBALS = {
    "pairs": "pairs", "ipairs": "ipairs", "next": "next", "type": "type",
    "tonumber": "tonumber", "tostring": "tostring", "select": "select",
    "unpack": "unpack", "pcall": "pcall", "xpcall": "xpcall", "error": "error",
    "assert": "assert", "rawget": "rawget", "rawset": "rawset",
    "rawequal": "rawequal", "setmetatable": "setmetatable",
    "getmetatable": "getmetatable", "print": "print", "date": "date",
    "time": "time", "format": "format", "wipe": "wipe", "strsplit": "strsplit",
    "strtrim": "strtrim", "strmatch": "strmatch", "strfind": "strfind",
    "strsub": "strsub", "strlower": "strlower", "strupper": "strupper",
    "strlen": "strlen", "strjoin": "strjoin", "strbyte": "strbyte",
    "strchar": "strchar", "gsub": "gsub", "tinsert": "tinsert",
    "tremove": "tremove", "floor": "floor", "ceil": "ceil", "abs": "abs",
    "min": "min", "max": "max", "sqrt": "sqrt", "random": "random",
    "geterrorhandler": "geterrorhandler", "debugprofilestart": "debugprofilestart",
    "debugprofilestop": "debugprofilestop", "debugstack": "debugstack",
}

WOW_API = {
    "UnitName": "UnitName", "UnitClass": "UnitClass", "UnitRace": "UnitRace",
    "UnitLevel": "UnitLevel", "UnitHealth": "UnitHealth",
    "UnitHealthMax": "UnitHealthMax", "UnitPower": "UnitPower",
    "UnitPowerMax": "UnitPowerMax", "UnitMana": "UnitMana",
    "UnitManaMax": "UnitManaMax", "UnitGUID": "UnitGUID", "UnitExists": "UnitExists",
    "UnitIsDead": "UnitIsDead", "UnitIsDeadOrGhost": "UnitIsDeadOrGhost",
    "UnitIsUnit": "UnitIsUnit", "UnitIsFriend": "UnitIsFriend",
    "UnitIsEnemy": "UnitIsEnemy", "UnitIsPlayer": "UnitIsPlayer",
    "UnitIsConnected": "UnitIsConnected", "UnitAffectingCombat": "UnitAffectingCombat",
    "UnitBuff": "UnitBuff", "UnitDebuff": "UnitDebuff", "UnitAura": "UnitAura",
    "UnitInRaid": "UnitInRaid", "UnitInParty": "UnitInParty",
    "UnitFactionGroup": "UnitFactionGroup", "UnitIsPartyLeader": "UnitIsPartyLeader",
    "UnitIsRaidOfficer": "UnitIsRaidOfficer", "UnitIsPVP": "UnitIsPVP",
    "UnitIsPVPFreeForAll": "UnitIsPVPFreeForAll", "UnitOnTaxi": "UnitOnTaxi",
    "UnitInVehicle": "UnitInVehicle", "UnitHasVehicleUI": "UnitHasVehicleUI",
    "UnitDetailedThreatSituation": "UnitDetailedThreatSituation",
    "UnitPlayerOrPetInRaid": "UnitPlayerOrPetInRaid",
    "UnitPlayerOrPetInParty": "UnitPlayerOrPetInParty",
    "GetUnitName": "GetUnitName", "GetSpellInfo": "GetSpellInfo",
    "GetSpellTexture": "GetSpellTexture", "GetSpellCooldown": "GetSpellCooldown",
    "GetInstanceInfo": "GetInstanceInfo", "IsInInstance": "IsInInstance",
    "IsInRaid": "IsInRaid", "IsInGroup": "IsInGroup",
    "GetNumGroupMembers": "GetNumGroupMembers", "GetNumRaidMembers": "GetNumRaidMembers",
    "GetNumPartyMembers": "GetNumPartyMembers",
    "GetRealNumRaidMembers": "GetRealNumRaidMembers",
    "GetRealNumPartyMembers": "GetRealNumPartyMembers",
    "GetRaidRosterInfo": "GetRaidRosterInfo", "GetTime": "GetTime",
    "GetTickCount": "GetTickCount", "CreateFrame": "CreateFrame",
    "GetScreenWidth": "GetScreenWidth", "GetScreenHeight": "GetScreenHeight",
    "GetCursorPosition": "GetCursorPosition", "PlaySoundFile": "PlaySoundFile",
    "PlaySound": "PlaySound", "SendChatMessage": "SendChatMessage",
    "SendAddonMessage": "SendAddonMessage", "InCombatLockdown": "InCombatLockdown",
    "IsFalling": "IsFalling", "IsMounted": "IsMounted",
    "GetActiveTalentGroup": "GetActiveTalentGroup", "GetMapInfo": "GetMapInfo",
    "GetCurrentMapAreaID": "GetCurrentMapAreaID",
    "GetCurrentMapDungeonLevel": "GetCurrentMapDungeonLevel",
    "GetRealZoneText": "GetRealZoneText", "GetSubZoneText": "GetSubZoneText",
    "SetMapToCurrentZone": "SetMapToCurrentZone",
    "GetPlayerMapPosition": "GetPlayerMapPosition", "GetGuildInfo": "GetGuildInfo",
    "GetNumGuildMembers": "GetNumGuildMembers",
    "GetGuildRosterInfo": "GetGuildRosterInfo", "IsInGuild": "IsInGuild",
    "GetNumFriends": "GetNumFriends", "GetFriendInfo": "GetFriendInfo",
    "GetAddOnInfo": "GetAddOnInfo", "GetAddOnMetadata": "GetAddOnMetadata",
    "GetNumAddOns": "GetNumAddOns", "IsAddOnLoaded": "IsAddOnLoaded",
    "LoadAddOn": "LoadAddOn", "GetRealmName": "GetRealmName",
    "GetLocale": "GetLocale", "IsShiftKeyDown": "IsShiftKeyDown",
    "IsControlKeyDown": "IsControlKeyDown", "IsAltKeyDown": "IsAltKeyDown",
    "InterfaceOptionsFrame_OpenToCategory": "InterfaceOptionsFrame_OpenToCategory",
    "StaticPopup_Show": "StaticPopup_Show", "ReloadUI": "ReloadUI",
    "UpdateAddOnMemoryUsage": "UpdateAddOnMemoryUsage",
    "GetAddOnMemoryUsage": "GetAddOnMemoryUsage",
    "UpdateAddOnCPUUsage": "UpdateAddOnCPUUsage",
    "GetFrameCPUUsage": "GetFrameCPUUsage", "SecondsToTime": "SecondsToTime",
    "UnitInBattleground": "UnitInBattleground", "IsOutdoors": "IsOutdoors",
}

# ============================================================
# Core Logic
# ============================================================
class Token:
    CODE, STRING, COMMENT, LONG_STRING, LONG_COMMENT = "code", "string", "comment", "long_string", "long_comment"
    def __init__(self, kind, text, start, end_):
        self.kind = kind
        self.text = text
        self.start = start
        self.end = end_

def tokenize_lua(source: str):
    tokens = []
    i, n, code_start = 0, len(source), 0
    while i < n:
        if source[i:i+4] == '--[=' or source[i:i+3] == '--[':
            j, eq_count = i + 2, 0
            while j < n and source[j] == '=':
                eq_count += 1
                j += 1
            if j < n and source[j] == '[':
                if i > code_start:
                    tokens.append(Token(Token.CODE, source[code_start:i], code_start, i))
                close_pattern = ']' + '=' * eq_count + ']'
                end_idx = source.find(close_pattern, j + 1)
                end_idx = n if end_idx == -1 else end_idx + len(close_pattern)
                tokens.append(Token(Token.LONG_COMMENT, source[i:end_idx], i, end_idx))
                i = code_start = end_idx
                continue

        if i + 1 < n and source[i] == '-' and source[i+1] == '-':
            if i > code_start:
                tokens.append(Token(Token.CODE, source[code_start:i], code_start, i))
            end_idx = source.find('\n', i)
            end_idx = n if end_idx == -1 else end_idx + 1
            tokens.append(Token(Token.COMMENT, source[i:end_idx], i, end_idx))
            i = code_start = end_idx
            continue

        if source[i] == '[':
            j, eq_count = i + 1, 0
            while j < n and source[j] == '=':
                eq_count += 1
                j += 1
            if j < n and source[j] == '[':
                if i > code_start:
                    tokens.append(Token(Token.CODE, source[code_start:i], code_start, i))
                close_pattern = ']' + '=' * eq_count + ']'
                end_idx = source.find(close_pattern, j + 1)
                end_idx = n if end_idx == -1 else end_idx + len(close_pattern)
                tokens.append(Token(Token.LONG_STRING, source[i:end_idx], i, end_idx))
                i = code_start = end_idx
                continue

        if source[i] in ('"', "'"):
            quote = source[i]
            if i > code_start:
                tokens.append(Token(Token.CODE, source[code_start:i], code_start, i))
            j = i + 1
            while j < n:
                if source[j] == '\\': j += 2
                elif source[j] == quote: j += 1; break
                elif source[j] == '\n': j += 1; break
                else: j += 1
            tokens.append(Token(Token.STRING, source[i:j], i, j))
            i = code_start = j
            continue
        i += 1

    if code_start < n:
        tokens.append(Token(Token.CODE, source[code_start:n], code_start, n))
    return tokens

def find_existing_locals(code_tokens):
    existing = set()
    full_code = ''.join(t.text for t in code_tokens if t.kind == Token.CODE)
    for m in re.finditer(r'\blocal\s+((?:[a-zA-Z_]\w*\s*,\s*)*[a-zA-Z_]\w*)\s*=\s*((?:(?:[a-zA-Z_]\w*\.)?[a-zA-Z_]\w*\s*,\s*)*(?:[a-zA-Z_]\w*\.)?[a-zA-Z_]\w*)', full_code):
        for name in m.group(1).split(','): existing.add(name.strip())
        for val in m.group(2).split(','): existing.add(val.strip())
    return existing

def find_global_usage(code_tokens, existing_locals):
    usage = defaultdict(int)
    full_code = ''.join(t.text for t in code_tokens if t.kind == Token.CODE)
    all_globals = {**LUA_STDLIB, **LUA_GLOBALS, **WOW_API}

    for g_name in all_globals:
        if g_name in existing_locals or all_globals[g_name] in existing_locals:
            continue
        if '.' in g_name:
            pattern = r'(?<![.\w:])' + re.escape(g_name) + r'(?=\s*[\(\[]|\s*$|\s*,|\s*\))'
            count = len(re.findall(pattern, full_code))
            if count > 0: usage[g_name] = count
        else:
            pattern = r'(?<![.\w:])' + re.escape(g_name) + r'(?![.\w])'
            count = len(re.findall(pattern, full_code))
            if count >= 2: usage[g_name] = count
    return dict(usage)

def generate_local_block(usage, min_uses=2):
    filtered = {k: v for k, v in usage.items() if v >= min_uses}
    if not filtered: return "", {}
    
    all_globals = {**LUA_STDLIB, **LUA_GLOBALS, **WOW_API}
    cats = {"Lua": [], "math": [], "string": [], "table": [], "bit": [], "WoW API": []}
    
    for g_name in sorted(filtered.keys()):
        l_name, count = all_globals[g_name], filtered[g_name]
        if g_name.startswith("math."): cats["math"].append((g_name, l_name))
        elif g_name.startswith("string."): cats["string"].append((g_name, l_name))
        elif g_name.startswith("table."): cats["table"].append((g_name, l_name))
        elif g_name.startswith("bit."): cats["bit"].append((g_name, l_name))
        elif g_name in LUA_GLOBALS: cats["Lua"].append((g_name, l_name))
        else: cats["WoW API"].append((g_name, l_name))

    lines = ["-- [LuaBoost Localizer] Auto-generated local references"]
    repl_map = {}
    for cat, entries in cats.items():
        if not entries: continue
        lines.append(f"-- {cat}")
        for g_name, l_name in entries:
            lines.append(f"local {l_name} = {g_name}")
            if '.' in g_name or l_name != g_name:
                repl_map[g_name] = l_name
    lines.extend(["-- [/LuaBoost Localizer]", ""])
    return '\n'.join(lines), repl_map

def find_injection_point(source):
    lines = source.split('\n')
    first_code = 0
    for i, line in enumerate(lines):
        if line.strip() == '' or line.strip().startswith('--'):
            first_code = i + 1
            continue
        break
    
    last_local = first_code
    for i in range(first_code, min(len(lines), 150)):
        s = lines[i].strip()
        if s.startswith('local '): last_local = i + 1
        elif s == '' or s.startswith('--'): continue
        elif last_local > first_code: break
        
    offset = sum(len(lines[i]) + 1 for i in range(min(last_local, len(lines))))
    return offset

def apply_replacements(source, repl_map):
    if not repl_map: return source
    tokens = tokenize_lua(source)
    res = []
    for t in tokens:
        if t.kind == Token.CODE:
            txt = t.text
            for g_name, l_name in sorted(repl_map.items(), key=lambda x: -len(x[0])):
                if '.' in g_name:
                    txt = re.sub(r'(?<![.\w:])' + re.escape(g_name) + r'(?![.\w])', l_name, txt)
            res.append(txt)
        else:
            res.append(t.text)
    return ''.join(res)

# ============================================================
# GUI Application
# ============================================================
class RedirectText(object):
    def __init__(self, text_widget):
        self.text_space = text_widget

    def write(self, string):
        self.text_space.config(state=tk.NORMAL)
        self.text_space.insert("end", string)
        self.text_space.see("end")
        self.text_space.config(state=tk.DISABLED)
        self.text_space.update_idletasks()

    def flush(self):
        pass

class LuaBoostApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"LuaBoost Localizer v{__version__}")
        self.root.geometry("700x550")
        self.root.minsize(600, 400)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(path_frame, text="AddOns Folder:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.path_var, width=50).pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="Browse...", command=self.browse_folder).pack(side=tk.LEFT)
        
        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.dry_run_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Dry Run (Preview only, don't modify files)", variable=self.dry_run_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.replace_dotted_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Replace dotted calls (math.floor -> math_floor)", variable=self.replace_dotted_var).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(opt_frame, text="Exclude Folders (comma separated):").grid(row=0, column=1, sticky=tk.E, padx=(20, 5))
        self.exclude_var = tk.StringVar(value="!LuaBoost,!Swatter,!Astrolabe,LibStub,Ace3,AceGUI")
        ttk.Entry(opt_frame, textvariable=self.exclude_var, width=25).grid(row=0, column=2, sticky=tk.W)

        ttk.Label(opt_frame, text="Min uses to localize:").grid(row=1, column=1, sticky=tk.E, padx=(20, 5))
        self.min_uses_var = tk.IntVar(value=2)
        ttk.Spinbox(opt_frame, from_=2, to=10, textvariable=self.min_uses_var, width=5).grid(row=1, column=2, sticky=tk.W)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_run = tk.Button(btn_frame, text="⚡ Optimize Addons", font=("Segoe UI", 11, "bold"), bg="#4CAF50", fg="white", command=self.start_optimization)
        self.btn_run.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5), ipady=5)
        
        self.btn_undo = tk.Button(btn_frame, text="↺ Undo All Changes", font=("Segoe UI", 11, "bold"), bg="#F44336", fg="white", command=self.start_undo)
        self.btn_undo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0), ipady=5)

        ttk.Label(main_frame, text="Log Output:").pack(anchor=tk.W)
        self.console = tk.Text(main_frame, wrap=tk.WORD, state=tk.DISABLED, bg="#1E1E1E", fg="#D4D4D4", font=("Consolas", 9))
        self.console.pack(fill=tk.BOTH, expand=True)
        
        scroll = ttk.Scrollbar(self.console, command=self.console.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=scroll.set)
        
        sys.stdout = RedirectText(self.console)
        
        print(f"Welcome to LuaBoost Localizer v{__version__}!")
        print("Please select your WoW/Interface/AddOns folder and click 'Optimize Addons'.")
        print("Backups (.lua.bak) are automatically created.\n")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select AddOns Folder")
        if folder:
            self.path_var.set(folder)

    def set_buttons_state(self, state):
        self.btn_run.config(state=state)
        self.btn_undo.config(state=state)

    def start_optimization(self):
        target = self.path_var.get().strip()
        if not target or not os.path.isdir(target):
            messagebox.showerror("Error", "Please select a valid AddOns directory.")
            return
        self.set_buttons_state(tk.DISABLED)
        threading.Thread(target=self.run_process, args=(target, False), daemon=True).start()

    def start_undo(self):
        target = self.path_var.get().strip()
        if not target or not os.path.isdir(target):
            messagebox.showerror("Error", "Please select a valid AddOns directory.")
            return
        if not messagebox.askyesno("Confirm Undo", "This will restore all .lua.bak files in the selected folder.\nAre you sure?"):
            return
        self.set_buttons_state(tk.DISABLED)
        threading.Thread(target=self.run_process, args=(target, True), daemon=True).start()

    def run_process(self, target_path, is_undo):
        try:
            if is_undo:
                self.do_undo(target_path)
            else:
                self.do_optimize(target_path)
        except Exception as e:
            print(f"\nCRITICAL ERROR: {str(e)}")
        finally:
            self.root.after(0, lambda: self.set_buttons_state(tk.NORMAL))

    def do_undo(self, target_path):
        print(f"\n{'='*60}\n  UNDOING CHANGES in {target_path}\n{'='*60}")
        count = 0
        for dirpath, _, filenames in os.walk(target_path):
            for filename in filenames:
                if filename.endswith('.lua.bak'):
                    bak_path = os.path.join(dirpath, filename)
                    lua_path = bak_path[:-4]
                    shutil.copy2(bak_path, lua_path)
                    os.remove(bak_path)
                    count += 1
                    print(f"  Restored: {os.path.relpath(lua_path, target_path)}")
        print(f"\nDone! Restored {count} files from backups.")

    def do_optimize(self, target_path):
        dry_run = self.dry_run_var.get()
        replace_dotted = self.replace_dotted_var.get()
        min_uses = self.min_uses_var.get()
        exclude = set(x.strip().lower() for x in self.exclude_var.get().split(',') if x.strip())

        print(f"\n{'='*60}\n  STARTING OPTIMIZATION\n{'='*60}")
        print(f"  Target: {target_path}")
        print(f"  Mode: {'DRY RUN' if dry_run else 'APPLY (Making Backups)'}")
        print(f"  Min uses: {min_uses}")
        print(f"  Replace dotted calls: {replace_dotted}")
        if exclude: print(f"  Excluding: {', '.join(exclude)}")
        print("="*60 + "\n")

        lua_files = []
        for dirpath, dirnames, filenames in os.walk(target_path):
            basename = os.path.basename(dirpath).lower()
            
            # Skip common library folders implicitly
            if basename in ('libs', 'lib', 'libraries', 'embeds', '.git', 'astrolabe'):
                dirnames.clear()
                continue
                
            rel_path = os.path.relpath(dirpath, target_path).lower()
            addon_name = rel_path.split(os.sep)[0] if os.sep in rel_path else rel_path
            
            # Skip excluded addon names completely
            if addon_name in exclude:
                dirnames.clear()
                continue
                
            for filename in filenames:
                lower_file = filename.lower()
                # Skip .lua files that are known to break (Libraries)
                if not lower_file.endswith('.lua'): continue
                if any(s in lower_file for s in ['locale', 'localization', 'locals.lua', 'enus.lua', 'kokr.lua', 'ruru.lua', 'dongle', 'libstub', 'callbackhandler']):
                    continue
                lua_files.append(os.path.join(dirpath, filename))

        print(f"Found {len(lua_files)} valid .lua files to scan...\n")

        stats = {"files": 0, "mod": 0, "skip": 0, "done": 0, "glob": 0, "calls": 0}

        for filepath in lua_files:
            rel_path = os.path.relpath(filepath, target_path)
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    source = f.read()
            except Exception as e:
                print(f"  ERROR reading {rel_path}: {e}")
                continue

            if len(source.strip()) < 50: continue
            if "-- [LuaBoost Localizer]" in source:
                stats["done"] += 1
                continue

            tokens = tokenize_lua(source)
            code_tokens = [t for t in tokens if t.kind == Token.CODE]
            if not code_tokens: continue

            existing = find_existing_locals(code_tokens)
            usage = find_global_usage(code_tokens, existing)
            useful = {k: v for k, v in usage.items() if v >= min_uses}

            stats["files"] += 1

            if not useful:
                stats["skip"] += 1
                continue

            local_block, repl_map = generate_local_block(useful, min_uses)
            if not local_block:
                stats["skip"] += 1
                continue

            inject_at = find_injection_point(source)
            
            # Fix from v1.0.0: Replace dotted calls in the original source FIRST
            modified_source = source
            if replace_dotted and repl_map:
                dotted = {k: v for k, v in repl_map.items() if '.' in k}
                if dotted:
                    modified_source = apply_replacements(source, dotted)
            
            # THEN insert the generated block so we don't replace its contents
            new_source = modified_source[:inject_at] + '\n' + local_block + '\n' + modified_source[inject_at:]

            stats["mod"] += 1
            stats["glob"] += len(useful)
            stats["calls"] += sum(useful.values())

            action = "WOULD MODIFY" if dry_run else "MODIFIED"
            print(f"  {action}: {rel_path} (+{len(useful)} globals, {sum(useful.values())} calls)")

            if not dry_run:
                bak_path = filepath + '.bak'
                if not os.path.exists(bak_path):
                    shutil.copy2(filepath, bak_path)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_source)

        print(f"\n{'='*60}\n  SUMMARY\n{'='*60}")
        print(f"  Files scanned:    {stats['files']}")
        print(f"  Files modified:   {stats['mod']}")
        print(f"  Already done:     {stats['done']}")
        print(f"  Globals cached:   {stats['glob']}")
        print(f"  Total API calls optimized: {stats['calls']}")
        if not dry_run and stats['mod'] > 0:
            print("\n  Optimization complete! Start WoW and check your FPS/Frametimes.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LuaBoostApp(root)
    root.mainloop()