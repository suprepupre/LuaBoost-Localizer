# ⚠️ LuaBoost Localizer (EXPERIMENTAL / ABANDONED)

**Automatic global-to-local optimizer for World of Warcraft 3.3.5a addon Lua files.**

> **🛑 WARNING: DO NOT USE THIS ON YOUR LIVE UI SETUP.**
> This project is kept public for educational purposes and as a Proof of Concept. Running this tool on complex addons (like DBM, WeakAuras, or ElvUI) **will break them** and cause hundreds of Lua errors.

---

## 📖 The Concept (Why we built this)

In Lua 5.1, accessing global variables (`GetTime`, `math.floor`, `UnitHealth`, etc.) requires a slow hash table lookup on every call. Caching them as `local` references speeds up execution by 10-30% for hot-path code.

The goal of this Python tool was to parse all `.lua` files in a user's AddOns folder, detect frequently used globals, and automatically inject `local GetTime = GetTime` at the top of the file, whilst replacing dotted calls (like `math.floor()` to `math_floor()`).

## 💥 Why It Failed (The Technical Limitations)

During testing, we discovered severe, unfixable limitations when modifying legacy WoW 3.3.5a addons automatically:

1. **The 200 Locals Limit:** Lua 5.1 has a hardcoded limit of 200 local variables per scope/function. Massive addons like `DBM-Core` already use ~180-190 locals. Injecting 30-40 new locals pushes the file over the limit, causing a fatal compile error: `main function has more than 200 local variables`.
2. **Scope Corruption:** Addons utilizing complex library structures (like `LibStub`, `Ace3`, or `DongleStub`) use strict `vararg` (`...`) and `upvalue` patterns. Injecting a block of code at the top shifts the scope and destroys the library initialization, resulting in `attempt to call upvalue (a nil value)` errors.
3. **Regex vs AST:** A regex/tokenizer-based approach cannot accurately predict where the safest injection point is inside complex closures (`do ... end` blocks or `setfenv` manipulations). A full Abstract Syntax Tree (AST) parser would be required.
4. **Chain Reactions:** Breaking one minor sub-module causes massive chain-reaction crashes across the entire UI.

## 💾 Usage (For Developers Only)

If you are a developer and want to see the code or test it on a *single, simple* addon:

```bash
# Preview what would change (safe, no modifications):
luaboost_localizer.exe "C:\WoW\Interface\AddOns\SimpleAddon" --dry-run

# Apply optimizations:
luaboost_localizer.exe "C:\WoW\Interface\AddOns\SimpleAddon"

# Undo everything (Restores .lua.bak files):
luaboost_localizer.exe "C:\WoW\Interface\AddOns\SimpleAddon" --undo
```

## 🛡️ Safer Alternatives

If you want to optimize your WoW 3.3.5a client safely, use my engine-level and runtime-level projects instead. They do not modify addon source code and are 100% safe:

- **[wow_optimize.dll](https://github.com/suprepupre/wow-optimize)**: Engine-level C++ DLL (mimalloc, precision timers, combat log pool fix).
- **[!LuaBoost](https://github.com/suprepupre/LuaBoost)**: Runtime Lua addon (Smart Incremental GC, UI Thrashing Protection, SpeedyLoad).

---

## 📜 License
MIT License.