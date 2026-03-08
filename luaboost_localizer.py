#!/usr/bin/env python3
"""
LuaBoost Localizer v1.0.0
Standalone tool to inject local references for global WoW API and Lua stdlib calls.

Usage:
    python luaboost_localizer.py [path_to_addons_folder]
    python luaboost_localizer.py                          # uses current directory
    python luaboost_localizer.py --dry-run                # preview without modifying files
    python luaboost_localizer.py --report-only             # just show stats, no changes
    python luaboost_localizer.py --exclude DBM-Core,Skada  # skip specific addons

Creates .lua.bak backup files before modifying anything.

Author: Suprematist (LuaBoost project)
License: MIT
"""

import os
import sys
import re
import argparse
import shutil
from collections import defaultdict
from typing import List, Dict, Set, Tuple, Optional

__version__ = "1.0.0"

# ============================================================
# WoW API + Lua stdlib global catalog
# ============================================================

# Format: "global_name": "suggested_local_name"
# Only includes functions that are commonly called in hot paths

LUA_STDLIB = {
    # math
    "math.floor": "math_floor",
    "math.ceil": "math_ceil",
    "math.abs": "math_abs",
    "math.min": "math_min",
    "math.max": "math_max",
    "math.sqrt": "math_sqrt",
    "math.sin": "math_sin",
    "math.cos": "math_cos",
    "math.random": "math_random",
    "math.huge": "math_huge",
    "math.pi": "math_pi",
    "math.fmod": "math_fmod",
    "math.log": "math_log",
    "math.pow": "math_pow",
    # string
    "string.format": "string_format",
    "string.find": "string_find",
    "string.match": "string_match",
    "string.gmatch": "string_gmatch",
    "string.gsub": "string_gsub",
    "string.sub": "string_sub",
    "string.len": "string_len",
    "string.byte": "string_byte",
    "string.char": "string_char",
    "string.rep": "string_rep",
    "string.reverse": "string_reverse",
    "string.lower": "string_lower",
    "string.upper": "string_upper",
    "string.split": "string_split",  # WoW extension
    # table
    "table.insert": "table_insert",
    "table.remove": "table_remove",
    "table.sort": "table_sort",
    "table.concat": "table_concat",
    "table.wipe": "table_wipe",  # WoW extension
    "table.getn": "table_getn",
    # bit
    "bit.band": "bit_band",
    "bit.bor": "bit_bor",
    "bit.bxor": "bit_bxor",
    "bit.bnot": "bit_bnot",
    "bit.lshift": "bit_lshift",
    "bit.rshift": "bit_rshift",
}

# Simple globals (no dot)
LUA_GLOBALS = {
    "pairs": "pairs",
    "ipairs": "ipairs",
    "next": "next",
    "type": "type",
    "tonumber": "tonumber",
    "tostring": "tostring",
    "select": "select",
    "unpack": "unpack",
    "pcall": "pcall",
    "xpcall": "xpcall",
    "error": "error",
    "assert": "assert",
    "rawget": "rawget",
    "rawset": "rawset",
    "rawequal": "rawequal",
    "setmetatable": "setmetatable",
    "getmetatable": "getmetatable",
    "print": "print",
    "date": "date",
    "time": "time",
    "format": "format",  # WoW global alias for string.format
    "wipe": "wipe",  # WoW global alias for table.wipe
    "strsplit": "strsplit",
    "strtrim": "strtrim",
    "strmatch": "strmatch",
    "strfind": "strfind",
    "strsub": "strsub",
    "strlower": "strlower",
    "strupper": "strupper",
    "strlen": "strlen",
    "strjoin": "strjoin",
    "strbyte": "strbyte",
    "strchar": "strchar",
    "gsub": "gsub",  # WoW global alias
    "tinsert": "tinsert",  # WoW global alias
    "tremove": "tremove",  # WoW global alias
    "floor": "floor",  # some addons use this
    "ceil": "ceil",
    "abs": "abs",
    "min": "min",
    "max": "max",
    "sqrt": "sqrt",
    "random": "random",
    "geterrorhandler": "geterrorhandler",
    "debugprofilestart": "debugprofilestart",
    "debugprofilestop": "debugprofilestop",
    "debugstack": "debugstack",
}

WOW_API = {
    # Unit info
    "UnitName": "UnitName",
    "UnitClass": "UnitClass",
    "UnitRace": "UnitRace",
    "UnitLevel": "UnitLevel",
    "UnitHealth": "UnitHealth",
    "UnitHealthMax": "UnitHealthMax",
    "UnitPower": "UnitPower",
    "UnitPowerMax": "UnitPowerMax",
    "UnitMana": "UnitMana",
    "UnitManaMax": "UnitManaMax",
    "UnitGUID": "UnitGUID",
    "UnitExists": "UnitExists",
    "UnitIsDead": "UnitIsDead",
    "UnitIsDeadOrGhost": "UnitIsDeadOrGhost",
    "UnitIsUnit": "UnitIsUnit",
    "UnitIsFriend": "UnitIsFriend",
    "UnitIsEnemy": "UnitIsEnemy",
    "UnitIsPlayer": "UnitIsPlayer",
    "UnitIsConnected": "UnitIsConnected",
    "UnitAffectingCombat": "UnitAffectingCombat",
    "UnitBuff": "UnitBuff",
    "UnitDebuff": "UnitDebuff",
    "UnitAura": "UnitAura",
    "UnitInRaid": "UnitInRaid",
    "UnitInParty": "UnitInParty",
    "UnitFactionGroup": "UnitFactionGroup",
    "UnitIsPartyLeader": "UnitIsPartyLeader",
    "UnitIsRaidOfficer": "UnitIsRaidOfficer",
    "UnitIsPVP": "UnitIsPVP",
    "UnitIsPVPFreeForAll": "UnitIsPVPFreeForAll",
    "UnitOnTaxi": "UnitOnTaxi",
    "UnitInVehicle": "UnitInVehicle",
    "UnitHasVehicleUI": "UnitHasVehicleUI",
    "UnitDetailedThreatSituation": "UnitDetailedThreatSituation",
    "UnitPlayerOrPetInRaid": "UnitPlayerOrPetInRaid",
    "UnitPlayerOrPetInParty": "UnitPlayerOrPetInParty",
    "GetUnitName": "GetUnitName",
    # Spell
    "GetSpellInfo": "GetSpellInfo",
    "GetSpellTexture": "GetSpellTexture",
    "GetSpellCooldown": "GetSpellCooldown",
    # Instance/Group
    "GetInstanceInfo": "GetInstanceInfo",
    "IsInInstance": "IsInInstance",
    "IsInRaid": "IsInRaid",
    "IsInGroup": "IsInGroup",
    "GetNumGroupMembers": "GetNumGroupMembers",
    "GetNumRaidMembers": "GetNumRaidMembers",
    "GetNumPartyMembers": "GetNumPartyMembers",
    "GetRealNumRaidMembers": "GetRealNumRaidMembers",
    "GetRealNumPartyMembers": "GetRealNumPartyMembers",
    "GetRaidRosterInfo": "GetRaidRosterInfo",
    # Time
    "GetTime": "GetTime",
    "GetTickCount": "GetTickCount",
    # UI
    "CreateFrame": "CreateFrame",
    "GetScreenWidth": "GetScreenWidth",
    "GetScreenHeight": "GetScreenHeight",
    "GetCursorPosition": "GetCursorPosition",
    "PlaySoundFile": "PlaySoundFile",
    "PlaySound": "PlaySound",
    "SendChatMessage": "SendChatMessage",
    "SendAddonMessage": "SendAddonMessage",
    # Combat
    "InCombatLockdown": "InCombatLockdown",
    "IsFalling": "IsFalling",
    "IsMounted": "IsMounted",
    # Talents/Spec
    "GetActiveTalentGroup": "GetActiveTalentGroup",
    # Map
    "GetMapInfo": "GetMapInfo",
    "GetCurrentMapAreaID": "GetCurrentMapAreaID",
    "GetCurrentMapDungeonLevel": "GetCurrentMapDungeonLevel",
    "GetRealZoneText": "GetRealZoneText",
    "GetSubZoneText": "GetSubZoneText",
    "SetMapToCurrentZone": "SetMapToCurrentZone",
    "GetPlayerMapPosition": "GetPlayerMapPosition",
    # Guild/Friends
    "GetGuildInfo": "GetGuildInfo",
    "GetNumGuildMembers": "GetNumGuildMembers",
    "GetGuildRosterInfo": "GetGuildRosterInfo",
    "IsInGuild": "IsInGuild",
    "GetNumFriends": "GetNumFriends",
    "GetFriendInfo": "GetFriendInfo",
    # Addon
    "GetAddOnInfo": "GetAddOnInfo",
    "GetAddOnMetadata": "GetAddOnMetadata",
    "GetNumAddOns": "GetNumAddOns",
    "IsAddOnLoaded": "IsAddOnLoaded",
    "LoadAddOn": "LoadAddOn",
    "GetRealmName": "GetRealmName",
    "GetLocale": "GetLocale",
    # Keys
    "IsShiftKeyDown": "IsShiftKeyDown",
    "IsControlKeyDown": "IsControlKeyDown",
    "IsAltKeyDown": "IsAltKeyDown",
    # Frame
    "InterfaceOptionsFrame_OpenToCategory": "InterfaceOptionsFrame_OpenToCategory",
    "StaticPopup_Show": "StaticPopup_Show",
    "ReloadUI": "ReloadUI",
    "UpdateAddOnMemoryUsage": "UpdateAddOnMemoryUsage",
    "GetAddOnMemoryUsage": "GetAddOnMemoryUsage",
    "UpdateAddOnCPUUsage": "UpdateAddOnCPUUsage",
    "GetFrameCPUUsage": "GetFrameCPUUsage",
    "SecondsToTime": "SecondsToTime",
    "UnitInBattleground": "UnitInBattleground",
    "IsOutdoors": "IsOutdoors",
}

# ============================================================
# Lua Tokenizer — handles strings, comments, long strings
# ============================================================

class Token:
    CODE = "code"
    STRING = "string"
    COMMENT = "comment"
    LONG_STRING = "long_string"
    LONG_COMMENT = "long_comment"

    def __init__(self, kind: str, text: str, start: int, end_: int):
        self.kind = kind
        self.text = text
        self.start = start
        self.end = end_


def tokenize_lua(source: str) -> List[Token]:
    """
    Splits Lua source into tokens, distinguishing code from strings and comments.
    This ensures we never modify content inside strings or comments.
    """
    tokens = []
    i = 0
    n = len(source)
    code_start = 0

    while i < n:
        # Long comment: --[=*[
        if source[i:i+4] == '--[=' or source[i:i+3] == '--[':
            # Check for long comment --[[ or --[==[
            j = i + 2
            eq_count = 0
            while j < n and source[j] == '=':
                eq_count += 1
                j += 1
            if j < n and source[j] == '[':
                # It's a long comment
                if i > code_start:
                    tokens.append(Token(Token.CODE, source[code_start:i], code_start, i))

                close_pattern = ']' + '=' * eq_count + ']'
                end_idx = source.find(close_pattern, j + 1)
                if end_idx == -1:
                    end_idx = n - len(close_pattern)
                end_idx += len(close_pattern)
                tokens.append(Token(Token.LONG_COMMENT, source[i:end_idx], i, end_idx))
                i = end_idx
                code_start = i
                continue

        # Short comment: --
        if i + 1 < n and source[i] == '-' and source[i+1] == '-':
            # Not a long comment (handled above)
            if i > code_start:
                tokens.append(Token(Token.CODE, source[code_start:i], code_start, i))
            end_idx = source.find('\n', i)
            if end_idx == -1:
                end_idx = n
            else:
                end_idx += 1  # include the newline
            tokens.append(Token(Token.COMMENT, source[i:end_idx], i, end_idx))
            i = end_idx
            code_start = i
            continue

        # Long string: [=*[
        if source[i] == '[':
            j = i + 1
            eq_count = 0
            while j < n and source[j] == '=':
                eq_count += 1
                j += 1
            if j < n and source[j] == '[':
                if i > code_start:
                    tokens.append(Token(Token.CODE, source[code_start:i], code_start, i))
                close_pattern = ']' + '=' * eq_count + ']'
                end_idx = source.find(close_pattern, j + 1)
                if end_idx == -1:
                    end_idx = n - len(close_pattern)
                end_idx += len(close_pattern)
                tokens.append(Token(Token.LONG_STRING, source[i:end_idx], i, end_idx))
                i = end_idx
                code_start = i
                continue

        # Quoted string: "..." or '...'
        if source[i] in ('"', "'"):
            quote = source[i]
            if i > code_start:
                tokens.append(Token(Token.CODE, source[code_start:i], code_start, i))
            j = i + 1
            while j < n:
                if source[j] == '\\':
                    j += 2  # skip escaped char
                elif source[j] == quote:
                    j += 1
                    break
                elif source[j] == '\n':
                    j += 1
                    break  # unterminated string
                else:
                    j += 1
            tokens.append(Token(Token.STRING, source[i:j], i, j))
            i = j
            code_start = i
            continue

        i += 1

    # Remaining code
    if code_start < n:
        tokens.append(Token(Token.CODE, source[code_start:n], code_start, n))

    return tokens


# ============================================================
# Analysis: find globals used in code tokens
# ============================================================

def find_existing_locals(code_tokens: List[Token]) -> Set[str]:
    """
    Scans code tokens for existing local declarations that alias globals.
    Detects patterns like:
        local floor = math.floor
        local GetTime = GetTime
        local pairs, ipairs, next = pairs, ipairs, next
        local tinsert, tremove = table.insert, table.remove
    """
    existing = set()
    full_code = ''.join(t.text for t in code_tokens if t.kind == Token.CODE)

    # Pattern: local <name> = <global>
    # Handles multi-assignment: local a, b, c = x, y, z
    for m in re.finditer(
        r'\blocal\s+'
        r'((?:[a-zA-Z_]\w*\s*,\s*)*[a-zA-Z_]\w*)'
        r'\s*=\s*'
        r'((?:(?:[a-zA-Z_]\w*\.)?[a-zA-Z_]\w*\s*,\s*)*(?:[a-zA-Z_]\w*\.)?[a-zA-Z_]\w*)',
        full_code
    ):
        names = [n.strip() for n in m.group(1).split(',')]
        values = [v.strip() for v in m.group(2).split(',')]
        for name in names:
            existing.add(name)
        for val in values:
            existing.add(val)  # track the RHS too, so we don't re-alias

    return existing


def find_global_usage(code_tokens: List[Token],
                      existing_locals: Set[str]) -> Dict[str, int]:
    """
    Counts how many times each global is used in code tokens.
    Only counts globals that are NOT already localized.
    """
    usage = defaultdict(int)
    full_code = ''.join(t.text for t in code_tokens if t.kind == Token.CODE)

    all_globals = {}
    all_globals.update(LUA_STDLIB)
    all_globals.update({k: v for k, v in LUA_GLOBALS.items()})
    all_globals.update({k: v for k, v in WOW_API.items()})

    for global_name, local_name in all_globals.items():
        # Skip if already localized
        if global_name in existing_locals or local_name in existing_locals:
            continue

        # For dotted names like "math.floor"
        if '.' in global_name:
            # Match math.floor( but NOT somevar.math.floor or :floor
            pattern = r'(?<![.\w:])' + re.escape(global_name) + r'(?=\s*[\(\[]|\s*$|\s*,|\s*\))'
            count = len(re.findall(pattern, full_code))
            if count > 0:
                usage[global_name] = count
        else:
            # Match GetTime( but NOT self.GetTime or :GetTime or local GetTime
            # Also match as function call or value reference
            pattern = r'(?<![.\w:])' + re.escape(global_name) + r'(?![.\w])'
            matches = re.findall(pattern, full_code)
            # Filter out 'local <name>' declarations
            count = 0
            for _ in matches:
                count += 1
            if count >= 2:  # Only localize if used 2+ times
                usage[global_name] = count

    return dict(usage)


# ============================================================
# Code Generation
# ============================================================

def generate_local_block(usage: Dict[str, int],
                         min_uses: int = 2) -> Tuple[str, Dict[str, str]]:
    """
    Generates a local declaration block and returns the replacement map.
    Groups by category for readability.
    """
    # Filter by minimum usage
    filtered = {k: v for k, v in usage.items() if v >= min_uses}
    if not filtered:
        return "", {}

    all_globals = {}
    all_globals.update(LUA_STDLIB)
    all_globals.update(LUA_GLOBALS)
    all_globals.update(WOW_API)

    # Categorize
    categories = {
        "Lua": [],
        "math": [],
        "string": [],
        "table": [],
        "bit": [],
        "WoW API": [],
    }

    for global_name in sorted(filtered.keys()):
        local_name = all_globals[global_name]
        count = filtered[global_name]

        if global_name.startswith("math."):
            categories["math"].append((global_name, local_name, count))
        elif global_name.startswith("string."):
            categories["string"].append((global_name, local_name, count))
        elif global_name.startswith("table."):
            categories["table"].append((global_name, local_name, count))
        elif global_name.startswith("bit."):
            categories["bit"].append((global_name, local_name, count))
        elif global_name in LUA_GLOBALS:
            categories["Lua"].append((global_name, local_name, count))
        else:
            categories["WoW API"].append((global_name, local_name, count))

    lines = []
    lines.append("-- [LuaBoost Localizer] Auto-generated local references")

    replacement_map = {}

    for cat_name, entries in categories.items():
        if not entries:
            continue
        lines.append(f"-- {cat_name}")
        for global_name, local_name, count in entries:
            if '.' in global_name:
                lines.append(f"local {local_name} = {global_name}")
                replacement_map[global_name] = local_name
            else:
                # For simple globals, use same name
                lines.append(f"local {local_name} = {global_name}")
                # Only add to replacement if name differs
                if local_name != global_name:
                    replacement_map[global_name] = local_name

    lines.append("-- [/LuaBoost Localizer]")
    lines.append("")

    return '\n'.join(lines), replacement_map


def find_injection_point(source: str) -> int:
    """
    Finds the best place to inject local declarations.
    Rules:
    1. After the last 'local ... = ...' block at the top of the file
    2. After any initial comments/header
    3. Before the first function definition
    """
    lines = source.split('\n')

    # Skip initial comments and blank lines
    first_code_line = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == '' or stripped.startswith('--'):
            first_code_line = i + 1
            continue
        break

    # Look for existing local declaration blocks (within first 100 lines)
    last_local_line = first_code_line
    scan_limit = min(len(lines), 150)

    for i in range(first_code_line, scan_limit):
        stripped = lines[i].strip()
        if stripped.startswith('local ') and '=' in stripped:
            last_local_line = i + 1
        elif stripped.startswith('local ') and '=' not in stripped:
            # local function or forward declaration
            last_local_line = i + 1
        elif stripped == '' or stripped.startswith('--'):
            continue
        elif last_local_line > first_code_line:
            # We've passed the local block
            break

    # Convert line number to character offset
    offset = 0
    for i in range(min(last_local_line, len(lines))):
        offset += len(lines[i]) + 1  # +1 for newline

    return offset


def apply_replacements(source: str, replacement_map: Dict[str, str]) -> str:
    """
    Replaces dotted globals (math.floor -> math_floor) in code tokens only.
    Does NOT replace inside strings or comments.
    """
    if not replacement_map:
        return source

    tokens = tokenize_lua(source)
    result = []

    for token in tokens:
        if token.kind == Token.CODE:
            text = token.text
            for global_name, local_name in sorted(replacement_map.items(),
                                                   key=lambda x: -len(x[0])):
                if '.' in global_name:
                    pattern = r'(?<![.\w:])' + re.escape(global_name) + r'(?![.\w])'
                    text = re.sub(pattern, local_name, text)
            result.append(text)
        else:
            result.append(token.text)

    return ''.join(result)


# ============================================================
# File Processing
# ============================================================

def has_localizer_block(source: str) -> bool:
    """Check if file already has our injected block."""
    return "-- [LuaBoost Localizer]" in source


def process_file(filepath: str, dry_run: bool = False,
                 min_uses: int = 2,
                 replace_dotted: bool = True) -> Optional[dict]:
    """
    Process a single .lua file.
    Returns stats dict or None if skipped.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
    except (IOError, OSError) as e:
        print(f"  ERROR reading {filepath}: {e}")
        return None

    # Skip empty files
    if len(source.strip()) < 50:
        return None

    # Skip if already processed
    if has_localizer_block(source):
        return {"status": "already_processed", "file": filepath}

    # Tokenize
    tokens = tokenize_lua(source)
    code_tokens = [t for t in tokens if t.kind == Token.CODE]

    if not code_tokens:
        return None

    # Find existing locals
    existing = find_existing_locals(code_tokens)

    # Find usage
    usage = find_global_usage(code_tokens, existing)

    # Filter by min uses
    useful = {k: v for k, v in usage.items() if v >= min_uses}

    if not useful:
        return {
            "status": "no_changes",
            "file": filepath,
            "existing_locals": len(existing),
        }

    # Generate local block
    local_block, replacement_map = generate_local_block(useful, min_uses)

    if not local_block:
        return {"status": "no_changes", "file": filepath}

    # Find injection point
    inject_at = find_injection_point(source)

    # Build new source
    new_source = source[:inject_at] + '\n' + local_block + '\n' + source[inject_at:]

    # Apply dotted replacements (math.floor -> math_floor)
    if replace_dotted and replacement_map:
        # Only replace dotted names, not simple same-name locals
        dotted_replacements = {k: v for k, v in replacement_map.items() if '.' in k}
        if dotted_replacements:
            new_source = apply_replacements(new_source, dotted_replacements)

    stats = {
        "status": "modified",
        "file": filepath,
        "globals_found": len(useful),
        "total_calls": sum(useful.values()),
        "existing_locals": len(existing),
        "details": useful,
        "replaced_dotted": len([k for k in replacement_map if '.' in k]) if replace_dotted else 0,
    }

    if not dry_run:
        # Create backup
        backup_path = filepath + '.bak'
        if not os.path.exists(backup_path):
            shutil.copy2(filepath, backup_path)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_source)

    return stats


def find_lua_files(root_dir: str, exclude: Set[str] = None) -> List[str]:
    """Recursively find all .lua files, excluding Libs/ folders."""
    exclude = exclude or set()
    lua_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip library folders
        basename = os.path.basename(dirpath)
        if basename.lower() in ('libs', 'lib', 'libraries', 'embeds', '.git'):
            dirnames.clear()
            continue

        # Check if this addon is excluded
        rel_path = os.path.relpath(dirpath, root_dir)
        addon_name = rel_path.split(os.sep)[0] if os.sep in rel_path else rel_path
        if addon_name in exclude:
            dirnames.clear()
            continue

        for filename in filenames:
            if filename.endswith('.lua'):
                # Skip locale/localization files
                lower = filename.lower()
                if any(skip in lower for skip in
                       ['locale', 'localization', 'locals.lua',
                        'enus.lua', 'kokr.lua', 'zhcn.lua', 'zhtw.lua',
                        'dede.lua', 'eses.lua', 'frfr.lua', 'ptbr.lua',
                        'ruru.lua', 'itit.lua']):
                    continue
                lua_files.append(os.path.join(dirpath, filename))

    return sorted(lua_files)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=f"LuaBoost Localizer v{__version__} — "
                    "Inject local references for WoW API globals in addon .lua files"
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Path to AddOns folder (default: current directory)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--report-only", action="store_true",
        help="Only show statistics, don't modify files"
    )
    parser.add_argument(
        "--min-uses", type=int, default=2,
        help="Minimum number of uses before localizing (default: 2)"
    )
    parser.add_argument(
        "--no-replace", action="store_true",
        help="Don't replace dotted calls (only inject locals)"
    )
    parser.add_argument(
        "--exclude", type=str, default="",
        help="Comma-separated list of addon folder names to skip"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed per-file output"
    )
    parser.add_argument(
        "--undo", action="store_true",
        help="Restore all .lua.bak files (undo all changes)"
    )

    args = parser.parse_args()

    target_path = os.path.abspath(args.path)

    if not os.path.isdir(target_path):
        print(f"ERROR: {target_path} is not a directory")
        sys.exit(1)

    # Undo mode
    if args.undo:
        count = 0
        for dirpath, _, filenames in os.walk(target_path):
            for filename in filenames:
                if filename.endswith('.lua.bak'):
                    bak_path = os.path.join(dirpath, filename)
                    lua_path = bak_path[:-4]  # remove .bak
                    shutil.copy2(bak_path, lua_path)
                    os.remove(bak_path)
                    count += 1
                    if args.verbose:
                        print(f"  Restored: {lua_path}")
        print(f"\nRestored {count} files from backups.")
        sys.exit(0)

    exclude = set(x.strip() for x in args.exclude.split(',') if x.strip())

    print(f"{'=' * 60}")
    print(f"  LuaBoost Localizer v{__version__}")
    print(f"  Scanning: {target_path}")
    if args.dry_run:
        print(f"  Mode: DRY RUN (no files will be modified)")
    elif args.report_only:
        print(f"  Mode: REPORT ONLY")
    else:
        print(f"  Mode: APPLY (backups will be created)")
    print(f"  Min uses: {args.min_uses}")
    if exclude:
        print(f"  Excluding: {', '.join(exclude)}")
    print(f"{'=' * 60}")
    print()

    lua_files = find_lua_files(target_path, exclude)
    print(f"Found {len(lua_files)} .lua files\n")

    total_files = 0
    modified_files = 0
    total_globals = 0
    total_calls = 0
    skipped_files = 0
    already_done = 0

    for filepath in lua_files:
        rel_path = os.path.relpath(filepath, target_path)

        result = process_file(
            filepath,
            dry_run=args.dry_run or args.report_only,
            min_uses=args.min_uses,
            replace_dotted=not args.no_replace
        )

        if result is None:
            continue

        total_files += 1

        if result["status"] == "already_processed":
            already_done += 1
            if args.verbose:
                print(f"  SKIP (already done): {rel_path}")

        elif result["status"] == "no_changes":
            skipped_files += 1
            if args.verbose:
                print(f"  SKIP (no globals):   {rel_path}"
                      f"  ({result.get('existing_locals', 0)} already localized)")

        elif result["status"] == "modified":
            modified_files += 1
            total_globals += result["globals_found"]
            total_calls += result["total_calls"]

            action = "WOULD MODIFY" if (args.dry_run or args.report_only) else "MODIFIED"
            print(f"  {action}: {rel_path}")
            print(f"    +{result['globals_found']} globals"
                  f" ({result['total_calls']} calls)"
                  f" | {result.get('existing_locals', 0)} already local"
                  f" | {result.get('replaced_dotted', 0)} dotted replaced")

            if args.verbose and result.get("details"):
                for name, count in sorted(result["details"].items(),
                                          key=lambda x: -x[1]):
                    print(f"      {name}: {count}x")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Summary")
    print(f"{'=' * 60}")
    print(f"  Files scanned:    {total_files}")
    print(f"  Files modified:   {modified_files}")
    print(f"  Files skipped:    {skipped_files}")
    print(f"  Already done:     {already_done}")
    print(f"  Globals localized:{total_globals}")
    print(f"  Total calls saved:{total_calls}")
    if not args.dry_run and not args.report_only and modified_files > 0:
        print(f"\n  Backups created as .lua.bak files")
        print(f"  To undo: python {os.path.basename(__file__)} --undo {args.path}")
    print()


if __name__ == "__main__":
    main()