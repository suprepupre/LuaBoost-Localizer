# LuaBoost Localizer

**Status:** Experimental / Abandoned  
**Target:** World of Warcraft 3.3.5a (Lua 5.1)  
**Purpose:** Automatic global-to-local variable optimizer for addon Lua files.

## Warning

This project is maintained for educational purposes and as a proof of concept. Running this tool on complex addons (DBM, WeakAuras, ElvUI) will likely break them and generate Lua errors. Do not use on live production UI setups.

## Concept

In Lua 5.1, accessing global variables requires a hash table lookup on every call. Caching frequently used globals as `local` references can improve execution speed by 10-30% in hot-path code.

This Python tool parses `.lua` files, detects high-frequency global usage, and automatically injects local reference declarations at the top of each file. It also replaces dotted calls (e.g., `math.floor()` becomes `math_floor()`) to bypass table indexing overhead.

## Technical Limitations

Automated modification of legacy WoW addons revealed several unresolvable issues:

1. **200 Local Variables Limit:** Lua 5.1 enforces a hardcoded limit of 200 local variables per function scope. Large addons like DBM-Core frequently approach 180-190 locals. Injecting additional references pushes files over the limit, causing fatal compilation errors: `main function has more than 200 local variables`.
2. **Scope Corruption:** Addons using library frameworks (LibStub, Ace3, DongleStub) rely on strict `vararg` (`...`) and `upvalue` patterns. Injecting code at the top of the file shifts scope boundaries, breaking library initialization and triggering `attempt to call upvalue (a nil value)` errors.
3. **Regex/Tokenizer Limitations:** The current implementation uses a custom tokenizer. It cannot accurately map complex closures, `setfenv` manipulations, or nested `do...end` blocks. A full Abstract Syntax Tree (AST) parser is required for safe injection.
4. **Dependency Chain Failures:** Modifying a single sub-module can trigger cascading failures across the entire UI framework.

## Usage (Developers Only)

This tool is intended for testing on isolated, simple addons.

```bash
# Preview changes (dry run, no file modifications)
luaboost_localizer.exe "C:\WoW\Interface\AddOns\SimpleAddon" --dry-run

# Apply optimizations
luaboost_localizer.exe "C:\WoW\Interface\AddOns\SimpleAddon"

# Restore original files from .lua.bak backups
luaboost_localizer.exe "C:\WoW\Interface\AddOns\SimpleAddon" --undo
```

## Safer Alternatives

For stable optimization of WoW 3.3.5a without modifying addon source code, consider these projects:

- **wow_optimize.dll**: Engine-level C++ optimization (mimalloc, precision timers, combat log pool fix).
- **!LuaBoost**: Runtime Lua addon (Smart Incremental GC, UI thrashing protection, SpeedyLoad).

## License

MIT License.