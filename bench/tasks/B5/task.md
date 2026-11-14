`Ledger` reads and writes its JSON file itself. We want a storage interface, so that tests and other tools can use a ledger without a file. Behaviour must not change.

Add `budgetbook/storage.py` with:

- `Storage`: an abstract base class with two methods, `load() -> dict | None` (the stored data, or None when nothing is stored yet) and `save(data: dict) -> None`. It cannot be instantiated itself.
- `JsonFileStorage(path)`: what `Ledger.load` and `Ledger.save` do today with the file. The file contents stay byte for byte the same. The write is atomic as today: the old file stays intact if the write fails and no temporary file is left behind. Missing parent folders are created. A missing file means `load()` returns None. A file that is not valid JSON, or not a JSON object, raises `LedgerFileError`.
- `MemoryStorage()`: keeps the data in memory. `load()` returns None until something was saved. It keeps a copy on `save` and returns a copy on `load`, so later changes to a dict do not leak in or out.

In `Ledger`, add `Ledger.from_storage(storage)` (an empty ledger when `load()` returns None) and `ledger.save_to(storage)`. `Ledger.load(path)` and `ledger.save(path)` stay and work as before, now through `JsonFileStorage`. `ledger.py` itself must no longer open files or import `json` or `os`. The check of the data format version stays in `Ledger`.
