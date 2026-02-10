#!/usr/bin/env python
"""
Clear the ChromaDB collection to fix embedding dimension mismatch.
Run this when you encounter "Collection expecting embedding with dimension X, got Y" errors.
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
        print("You can now run ingestion again with the correct embedding model.")

    except Exception as e:
        print(f"[ERROR] Error clearing ChromaDB: {e}")
        return False

    return True

def check_embedding_model():
    """Check which embedding model is configured."""
    import yaml

    config_path = Path("profiles/stripe/config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        embedding_config = config.get('model', {}).get('embedding', {})
        model_name = embedding_config.get('hf_name', 'Unknown')

        print(f"\n[INFO] Current embedding model configuration:")
        print(f"   Model: {model_name}")

        # Common embedding models and their dimensions
        model_dims = {
            'BAAI/bge-base-en-v1.5': 768,
            'BAAI/bge-small-en-v1.5': 384,
            'sentence-transformers/all-MiniLM-L6-v2': 384,
            'sentence-transformers/all-mpnet-base-v2': 768,
        }

        if model_name in model_dims:
            print(f"   Expected dimension: {model_dims[model_name]}")

        print("\n[NOTE] If you want to use a different model, update config.yaml")
        print("   Common models:")
        for model, dim in model_dims.items():
            print(f"     - {model} (dim: {dim})")

if __name__ == "__main__":
    print("=" * 60)
    print("CHROMADB COLLECTION CLEANER")
    print("=" * 60)

    # Check current configuration
    check_embedding_model()

    print("\n" + "=" * 60)

    # Ask for confirmation
    response = input("\nDo you want to clear the ChromaDB collection? (y/n): ")

    if response.lower() == 'y':
        clear_chroma_collection("stripe")
    else:
        print("Cancelled.")