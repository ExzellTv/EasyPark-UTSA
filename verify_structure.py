import os, importlib, sys

required = [
    "app/__init__.py",
    "app/routers/__init__.py",
    "app/services/__init__.py",
    "app/routers/parking.py",
    "app/services/vision.py",
    "data/spots.json",
]

print("🔍 Verifying project structure...\n")

for f in required:
    if os.path.exists(f):
        print(f"✅ {f} found")
    else:
        print(f"❌ {f} MISSING")

print("\n🔍 Verifying Python imports...")

try:
    importlib.import_module("app.routers.parking")
    importlib.import_module("app.services.vision")
    print("✅ Imports resolved successfully")
except Exception as e:
    print("❌ Import failed:", e)
    sys.exit(1)

print("\n✅ All structure checks passed!")
