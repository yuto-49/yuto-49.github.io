"""
Setup script for RAG system
Runs data collection and indexing in the correct order.
"""

import asyncio
from pathlib import Path


def main():
    print("\n" + "="*70)
    print("🚀 RAG System Setup for AI Career Agents")
    print("="*70)

    # Step 1: Collect data
    print("\n📚 Step 1: Collecting real-world job examples...")
    print("   This will fetch job descriptions and career information from the web.")

    try:
        from data_collector import collect_all_examples
        asyncio.run(collect_all_examples())
    except Exception as e:
        print(f"\n❌ Error during data collection: {e}")
        print("   You can skip this step and add your own data manually to:")
        print("   backend/data/company_examples/*.jsonl")

    # Step 2: Index data
    print("\n🗄️  Step 2: Indexing data with ChromaDB...")
    print("   This creates vector embeddings for semantic search.")

    try:
        from rag_system import CareerRAG
        rag = CareerRAG()
        results = rag.index_all()

        total_chunks = sum(results.values())
        if total_chunks == 0:
            print("\n⚠️  Warning: No data was indexed!")
            print("   Make sure you have .jsonl files in backend/data/company_examples/")
        else:
            print(f"\n✅ Successfully indexed {total_chunks} chunks!")

    except Exception as e:
        print(f"\n❌ Error during indexing: {e}")
        return False

    # Step 3: Test the system
    print("\n🧪 Step 3: Testing RAG search...")

    try:
        from rag_system import CareerRAG
        rag = CareerRAG()

        test_query = "Python machine learning data analysis"
        print(f"\n   Test query: '{test_query}'")

        for career_path in ["finance", "healthcare", "consultant"]:
            results = rag.search(career_path, test_query, top_k=1)

            if results:
                print(f"\n   ✓ {career_path.title()}: Found {len(results)} relevant examples")
                print(f"      Top result: {results[0]['title'][:60]}...")
            else:
                print(f"\n   ⚠️  {career_path.title()}: No results found")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")

    print("\n" + "="*70)
    print("✅ RAG Setup Complete!")
    print("="*70)
    print("\nYour AI Career Agents will now cite real-world job examples!")
    print("\nNext steps:")
    print("  1. Start your backend: python backend/app.py")
    print("  2. Open your portfolio in a browser")
    print("  3. Try the AI Career Agents section")
    print("\n" + "="*70 + "\n")

    return True


if __name__ == "__main__":
    main()
