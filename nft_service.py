import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
import httpx

class NFTNetworkService:
    """
    NFT Network Service for creating interactive network graphs
    Focuses on the top 1000 collections and their holder relationships
    """
    
    def __init__(self):
        self.base_url = "https://api-mainnet.magiceden.dev/v3/rtp/monad-testnet"
        self.headers = {
            "accept": "*/*",
            # Note: Add your API key here if you have one
            # "Authorization": "Bearer YOUR_API_KEY"
        }
        
        # Alchemy API configuration for getting real holder data
        self.alchemy_base_url = "https://monad-testnet.g.alchemy.com/nft/v3/utygy3hPZ0dLRNiSUMLWbiJKCem5l6Yl"
        self.alchemy_headers = {
            "accept": "application/json"
        }
        
        # Cache for expensive operations
        self.collections_cache = None
        self.holder_overlap_cache = {}
        self.holders_cache = {}  # Cache holders to avoid repeated API calls
        
    async def get_top_collections(self, limit: int = 1000) -> List[Dict]:
        """
        Fetch top collections by 30-day volume with pagination
        """
        if self.collections_cache and len(self.collections_cache) >= limit:
            return self.collections_cache[:limit]
            
        print(f"🔍 Fetching top {limit} collections by 30-day volume...")
        
        all_collections = []
        continuation_token = None
        limit_per_page = 20  # API limit
        
        try:
            while len(all_collections) < limit:
                # Build request URL
                url = f"{self.base_url}/collections/v7"
                params = {
                    "sortBy": "30DayVolume",  # Sort by 30-day volume
                    "limit": limit_per_page,
                    "includeMintStages": "false",
                    "includeSecurityConfigs": "false",
                    "normalizeRoyalties": "false",
                    "useNonFlaggedFloorAsk": "false"
                }
                
                if continuation_token:
                    params["continuation"] = continuation_token
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params, headers=self.headers)
                    
                    # Handle rate limiting (429 Too Many Requests)
                    if response.status_code == 429:
                        print("⚠️  Rate limit hit, waiting 60 seconds...")
                        await asyncio.sleep(60)
                        continue
                    
                    response.raise_for_status()
                    
                    data = response.json()
                    new_collections = data.get('collections', [])
                    
                    if not new_collections:
                        print("No more collections found")
                        break
                    
                    all_collections.extend(new_collections)
                    continuation_token = data.get('continuation')
                    
                    print(f"📊 Fetched {len(all_collections)} collections so far... (Rate: 1 req/sec)")
                    
                    if not continuation_token:
                        print("Reached end of collections list")
                        break
                    
                    # Rate limiting: Magic Eden API - 1.5 seconds between requests
                    await asyncio.sleep(1.5)
                    
        except Exception as e:
            print(f"❌ Error fetching collections: {e}")
            return []
        
        # Clean and sort data
        unique_collections = {col['id']: col for col in all_collections}.values()
        sorted_collections = sorted(
            unique_collections,
            key=lambda col: col.get('volume', {}).get('30day', 0),
            reverse=True
        )
        
        self.collections_cache = sorted_collections[:limit]
        print(f"✅ Successfully fetched and cached {len(self.collections_cache)} collections")
        
        return self.collections_cache
    
    async def get_collection_holders(self, collection_id: str) -> Set[str]:
        """
        Get real holders for a specific collection using Alchemy API
        """
        # Check cache first
        if collection_id in self.holders_cache:
            return self.holders_cache[collection_id]
        
        print(f"🔍 Fetching holders for collection {collection_id[:10]}...")
        
        holders = set()
        page_key = None
        
        try:
            while True:
                # Build Alchemy API URL
                url = f"{self.alchemy_base_url}/getOwnersForContract"
                params = {
                    "contractAddress": collection_id,
                    "withTokenBalances": "false"  # We only need owner addresses
                }
                
                if page_key:
                    params["pageKey"] = page_key
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params, headers=self.alchemy_headers)
                    
                    # Handle rate limiting
                    if response.status_code == 429:
                        print("⚠️  Alchemy rate limit hit, waiting 60 seconds...")
                        await asyncio.sleep(60)
                        continue
                    
                    if response.status_code != 200:
                        print(f"⚠️  Alchemy API error {response.status_code} for {collection_id[:10]}")
                        break
                    
                    data = response.json()
                    owners = data.get('owners', [])
                    
                    if not owners:
                        break
                    
                    # Process owners - Alchemy returns array of address strings
                    for owner in owners:
                        if isinstance(owner, str) and owner.startswith('0x'):
                            holders.add(owner.lower())
                        elif isinstance(owner, dict) and 'ownerAddress' in owner:
                            # Fallback for different response format
                            owner_address = owner.get('ownerAddress')
                            if owner_address and owner_address.startswith('0x'):
                                holders.add(owner_address.lower())
                    
                    # Check for pagination
                    page_key = data.get('pageKey')
                    if not page_key:
                        break
                    
                    # Rate limiting: Alchemy API - 1.5 seconds between requests
                    await asyncio.sleep(1.5)
                    
        except Exception as e:
            print(f"❌ Error fetching holders for {collection_id[:10]}: {e}")
            # Return empty set if API fails - better than mock data for real analysis
            holders = set()
        
        # Cache the results
        self.holders_cache[collection_id] = holders
        print(f"✅ Found {len(holders)} real holders for {collection_id[:10]}")
        
        return holders
    
    def calculate_holder_overlap(self, holders1: Set[str], holders2: Set[str]) -> Dict[str, int]:
        """
        Calculate overlap between two sets of holders
        """
        intersection = holders1.intersection(holders2)
        
        return {
            "shared_holders": len(intersection),
            "total_holders_1": len(holders1),
            "total_holders_2": len(holders2),
            "overlap_percentage": (len(intersection) / min(len(holders1), len(holders2))) * 100 if holders1 and holders2 else 0
        }
    
    async def build_network_graph(self, collections: List[Dict], min_shared_holders: int = 10) -> Dict:
        """
        Build network graph data with nodes and edges
        """
        print(f"🕸️  Building network graph with {len(collections)} collections...")
        print(f"📊 Minimum shared holders threshold: {min_shared_holders}")
        
        # Prepare nodes
        nodes = []
        collection_holders = {}
        
        # Get holders for each collection using real Alchemy API data
        print("🔍 Fetching real holder data from Alchemy API...")
        for i, collection in enumerate(collections):
            collection_id = collection['id']
            holders = await self.get_collection_holders(collection_id)
            collection_holders[collection_id] = holders
            
            # Calculate node size based on total holders
            node_size = len(holders)
            
            # Skip collections with no holders (API failed or truly empty)
            if node_size == 0:
                print(f"⚠️  Skipping {collection.get('name', 'Unknown')} - no holders found")
                continue
            
            node = {
                "id": collection_id,
                "name": collection.get('name', 'Unknown'),
                "symbol": collection.get('symbol', 'unknown'),
                "image": collection.get('image', ''),
                "holders": len(holders),
                "volume_30d": collection.get('volume', {}).get('30day', 0),
                "volume_all": collection.get('volume', {}).get('allTime', 0),
                "floor_price": self._extract_floor_price(collection),
                "token_count": int(collection.get('tokenCount', 0)),
                "market_cap": self._calculate_market_cap(collection),
                "size": min(max(node_size / 20, 8), 40),  # Adjust size based on real holder counts
                "verified": collection.get('magicedenVerificationStatus') == 'verified'
            }
            
            nodes.append(node)
            
            if (i + 1) % 10 == 0:
                print(f"📈 Processed {i + 1}/{len(collections)} collections (fetched {node_size} holders)...")
        
        # Calculate edges (connections between collections)
        print("🔗 Calculating connections between collections...")
        edges = []
        total_comparisons = len(collections) * (len(collections) - 1) // 2
        comparisons_done = 0
        
        for i, collection1 in enumerate(collections):
            for j, collection2 in enumerate(collections[i+1:], i+1):
                id1, id2 = collection1['id'], collection2['id']
                
                holders1 = collection_holders[id1]
                holders2 = collection_holders[id2]
                
                overlap = self.calculate_holder_overlap(holders1, holders2)
                
                if overlap['shared_holders'] >= min_shared_holders:
                    edge = {
                        "source": id1,
                        "target": id2,
                        "weight": overlap['shared_holders'],
                        "overlap_percentage": overlap['overlap_percentage']
                    }
                    edges.append(edge)
                
                comparisons_done += 1
                if comparisons_done % 1000 == 0:
                    progress = (comparisons_done / total_comparisons) * 100
                    print(f"🔍 Connection analysis: {progress:.1f}% complete ({comparisons_done}/{total_comparisons})")
        
        # Update node sizes based on degree (number of connections)
        node_degrees = defaultdict(int)
        for edge in edges:
            node_degrees[edge['source']] += edge['weight']
            node_degrees[edge['target']] += edge['weight']
        
        # Update node sizes based on influence (total shared holders)
        for node in nodes:
            influence = node_degrees.get(node['id'], 0)
            node['influence'] = influence
            node['size'] = min(max(influence / 50, 5), 50)  # Normalize based on influence
        
        print(f"✅ Network graph complete: {len(nodes)} nodes, {len(edges)} edges")
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_collections": len(nodes),
                "total_connections": len(edges),
                "min_shared_holders": min_shared_holders,
                "avg_connections_per_collection": len(edges) * 2 / len(nodes) if nodes else 0
            }
        }
    
    def _extract_floor_price(self, collection: Dict) -> float:
        """Extract floor price from collection data"""
        floor_ask = collection.get('floorAsk', {})
        if floor_ask and floor_ask.get('price'):
            return float(floor_ask['price'].get('amount', {}).get('native', 0))
        return 0.0
    
    def _calculate_market_cap(self, collection: Dict) -> float:
        """Calculate market cap (floor price * token count)"""
        floor_price = self._extract_floor_price(collection)
        token_count = int(collection.get('tokenCount', 0))
        return floor_price * token_count
    
    async def get_collection_details(self, collection_id: str) -> Dict:
        """
        Get detailed information for a specific collection
        """
        # First try to find in cache
        if self.collections_cache:
            for collection in self.collections_cache:
                if collection['id'] == collection_id:
                    return self._format_collection_details(collection)
        
        # If not in cache, fetch individually
        try:
            url = f"{self.base_url}/collections/{collection_id}/v7"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers)
                
                # Handle rate limiting (429 Too Many Requests)
                if response.status_code == 429:
                    print("⚠️  Rate limit hit for collection details, waiting 60 seconds...")
                    await asyncio.sleep(60)
                    # Retry the request
                    response = await client.get(url, headers=self.headers)
                
                response.raise_for_status()
                
                collection = response.json()
                return self._format_collection_details(collection)
                
        except Exception as e:
            print(f"❌ Error fetching collection details: {e}")
            return {}
    
    def _format_collection_details(self, collection: Dict) -> Dict:
        """Format collection data for detailed view"""
        volume = collection.get('volume', {})
        
        return {
            "id": collection.get('id'),
            "name": collection.get('name', 'Unknown'),
            "symbol": collection.get('symbol', 'unknown'),
            "image": collection.get('image', ''),
            "description": collection.get('description', ''),
            "floor_price": self._extract_floor_price(collection),
            "market_cap": self._calculate_market_cap(collection),
            "volume": {
                "1day": volume.get('1day', 0),
                "7day": volume.get('7day', 0),
                "30day": volume.get('30day', 0),
                "all_time": volume.get('allTime', 0)
            },
            "token_count": int(collection.get('tokenCount', 0)),
            "owner_count": int(collection.get('ownerCount', 0)),
            "listed_count": int(collection.get('onSaleCount', 0)),
            "verified": collection.get('magicedenVerificationStatus') == 'verified',
            "created_at": collection.get('createdAt'),
            "magic_eden_url": f"https://magiceden.io/collections/monad-testnet/{collection.get('symbol', '')}"
        }

# Global service instance
nft_network_service = NFTNetworkService()

async def get_network_graph_data(limit: int = 1000, min_shared_holders: int = 10) -> Dict:
    """
    Main function to get network graph data
    """
    print(f"🚀 Starting network graph generation...")
    print(f"📊 Collections limit: {limit}")
    print(f"🔗 Min shared holders: {min_shared_holders}")
    
    # Get top collections
    collections = await nft_network_service.get_top_collections(limit=limit)
    
    if not collections:
        return {"error": "Failed to fetch collections"}
    
    # Build network graph
    graph_data = await nft_network_service.build_network_graph(
        collections, 
        min_shared_holders=min_shared_holders
    )
    
    return {
        "graph": graph_data,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "data_source": "magic_eden_api",
            "collections_analyzed": len(collections),
            "parameters": {
                "limit": limit,
                "min_shared_holders": min_shared_holders
            }
        }
    }

# Test function
async def test_network_service():
    """Test the network service"""
    print("🧪 Testing NFT Network Service...")
    
    # Test with small dataset first
    data = await get_network_graph_data(limit=20, min_shared_holders=5)
    
    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return
    
    graph = data["graph"]
    print(f"✅ Test successful!")
    print(f"📊 Nodes: {len(graph['nodes'])}")
    print(f"🔗 Edges: {len(graph['edges'])}")
    print(f"📈 Stats: {graph['stats']}")
    
    # Save test data
    with open('test_network_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("💾 Test data saved to 'test_network_data.json'")

if __name__ == "__main__":
    asyncio.run(test_network_service()) 