
import asyncio
import asyncpg
import sys

async def test_conn(host, port, user, password, database):
    dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    print(f"Testing {host}:{port}...")
    try:
        conn = await asyncio.wait_for(asyncpg.connect(dsn), timeout=5)
        print(f"SUCCESS: Connected to {host}:{port}")
        await conn.close()
        return True
    except Exception as e:
        print(f"FAILED: {host}:{port} -> {type(e).__name__}: {e}")
        return False

async def main():
    regions = ["us-east-1", "us-east-2", "sa-east-1", "us-west-2", "us-west-1"]
    user = "postgres.vlghiwiwoftzbityvest"
    pw = "Santidevs2212"
    db = "postgres"
    
    for r in regions:
        host = f"aws-0-{r}.pooler.supabase.com"
        # Test session port 5432
        await test_conn(host, 5432, user, pw, db)
        # Test transaction port 6543
        await test_conn(host, 6543, user, pw, db)

if __name__ == "__main__":
    asyncio.run(main())
