"""
Fetch hospitals from OpenStreetMap and populate the cache.
This gives us 10,000+ hospitals for free with NO API key required.

Run: python -m app.db.fetch_osm_hospitals
"""
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Fetch all Indian hospitals from OSM and cache them."""
    from app.services.hospital_cache import refresh_hospital_cache, get_cache_meta
    
    print("=" * 70)
    print("🏥 RapidCare AI - OpenStreetMap Hospital Fetcher")
    print("=" * 70)
    print()
    print("This will fetch 10,000+ hospitals from OpenStreetMap Overpass API.")
    print("⏱️  Estimated time: 3-5 minutes")
    print("📡 No API key required - completely free!")
    print()
    print("Starting fetch...")
    print()
    
    try:
        # Refresh the cache (this will fetch from OSM)
        count = await refresh_hospital_cache(force=True)
        
        print()
        print("=" * 70)
        print(f"✅ SUCCESS! Fetched and cached {count:,} hospitals")
        print("=" * 70)
        print()
        
        # Show cache metadata
        meta = await get_cache_meta()
        print("📊 Cache Metadata:")
        for key, value in meta.items():
            print(f"   {key}: {value}")
        print()
        print("🎉 Your RapidCare AI system now has access to 10,000+ hospitals!")
        print("🔄 Cache will auto-refresh every 24 hours")
        print()
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ ERROR: {e}")
        print("=" * 70)
        print()
        print("💡 Troubleshooting:")
        print("   1. Check your internet connection")
        print("   2. Verify Redis is running (redis-server)")
        print("   3. Check Overpass API status: https://overpass-api.de/api/status")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
