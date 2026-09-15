from pathlib import Path

for path in [Path("data/asteria.db")]:
    path.unlink(missing_ok=True)
for directory in [Path("data/uploads"), Path("data/exports")]:
    if directory.exists():
        for item in directory.iterdir():
            if item.is_file() and item.name != ".gitkeep":
                item.unlink()
print("Local runtime data reset.")
