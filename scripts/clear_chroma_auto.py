#!/usr/bin/env python
"""
Automatically clear the ChromaDB collection without prompting.
"""

import chromadb
from chromadb.config import Settings
from pathlib import Path
import shutil

def clear_chroma_collection(profile_name="stripe"):
    """Clear the ChromaDB collection for a profile."""

    chroma_path = Path(f"profiles/{profile_name}/data/chroma")

    print(f"Clearing ChromaDB for profile: {profile_name}")
    print(f"Path: {chroma_path}")

    try:
        # Method 1: Try to delete the collection through ChromaDB API
        try:
            client = chromadb.Client(Settings(
                is_persistent=True,
                persist_directory=str(chroma_path)
            ))

            # Try to delete the collection
            try:
                client.delete_collection(name="docs")
                print("[OK] Deleted 'docs' collection via ChromaDB API")
            except:
                print("[WARNING] Collection 'docs' not found or couldn't be deleted via API")

        except Exception as e:
            print(f"[WARNING] ChromaDB client error: {e}")

        # Method 2: Clear the directory
        if chroma_path.exists():
            # Remove all files and subdirectories
            for item in chroma_path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print("[OK] Cleared ChromaDB directory")
        else:
            print("[WARNING] ChromaDB directory doesn't exist")

        # Recreate the empty directory
        chroma_path.mkdir(parents=True, exist_ok=True)
        print("[OK] Recreated empty ChromaDB directory")

        print("\n[SUCCESS] ChromaDB cleared successfully!")
        print("You can now run ingestion again.")

    except Exception as e:
        print(f"[ERROR] Error clearing ChromaDB: {e}")
        return False

    return True

if __name__ == "__main__":
    print("=" * 60)
    print("CHROMADB COLLECTION CLEANER")
    print("=" * 60)

    # Automatically clear without prompting
    clear_chroma_collection("stripe")

    print("\n" + "=" * 60)
    print("DONE - You can now run: python test_ingestion.py")
    print("=" * 60)