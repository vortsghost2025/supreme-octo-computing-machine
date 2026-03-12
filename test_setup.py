"""
Test script to verify SNAC-v2 setup
"""

import asyncio
import httpx
import json

async def test_backend():
    """Test the backend API endpoints."""
    base_url = "http://localhost:8000"
    
    print("Testing SNAC-v2 Backend...")
    
    # Test health endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Health check: {data['status']}")
            else:
                print(f"✗ Health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Cannot connect to backend: {e}")
        print("  Make sure to run: docker compose up -d")
        return False
    
    # Test ingest endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/ingest",
                json={"content": "The capital of Japan is Tokyo. 2+2=4."}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Ingest: {data['chunks']} chunks, ID: {data['document_id'][:8]}...")
            else:
                print(f"✗ Ingest failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Ingest error: {e}")
        return False
    
    # Test agent run endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/agent/run",
                json={"task": "QUERY: What is the capital of Japan? Then CALC: 25 * 4"}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Agent run: {data['result']} (tokens: {data['tokens_used']}, cost: ${data['cost']:.4f})")
            else:
                print(f"✗ Agent run failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Agent run error: {e}")
        return False
    
    # Test timeline endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/memory/timeline")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Timeline: {len(data['events'])} events")
            else:
                print(f"✗ Timeline failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Timeline error: {e}")
        return False
    
    # Test token usage endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/tokens/usage")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Token usage: ${data['total']:.4f} total")
            else:
                print(f"✗ Token usage failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Token usage error: {e}")
        return False
    
    print("\n✓ All tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_backend())
    exit(0 if success else 1)
