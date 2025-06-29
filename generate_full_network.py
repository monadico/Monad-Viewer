#!/usr/bin/env python3

import asyncio
import json
import time
from datetime import datetime
from nft_service import get_network_graph_data

async def generate_full_network():
    """
    Generate the full 1000 collection network graph with real holder data
    """
    print("🚀 Generating Full Monad NFT Ecosystem Network (1000 Collections)")
    print("=" * 80)
    print("⏱️  Expected time: 25-30 minutes (due to API rate limiting)")
    print("📊 This will fetch real holder data for each collection")
    print("🔗 Then analyze shared holders to build network connections")
    print()
    
    start_time = time.time()
    
    # Configuration
    limit = 1000
    min_shared_holders = 5  # Minimum shared holders to create an edge
    
    print(f"📋 Configuration:")
    print(f"   • Collections to analyze: {limit}")
    print(f"   • Minimum shared holders for connection: {min_shared_holders}")
    print(f"   • Rate limiting: 1.5 seconds between requests for both APIs")
    print()
    
    try:
        print("🔍 Starting network graph generation...")
        
        # Generate the full network
        result = await get_network_graph_data(
            limit=limit, 
            min_shared_holders=min_shared_holders
        )
        
        if "error" in result:
            print(f"❌ Error generating network: {result['error']}")
            return
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Extract results
        graph = result["graph"]
        metadata = result["metadata"]
        
        nodes = graph["nodes"]
        edges = graph["edges"]
        stats = graph["stats"]
        
        print(f"\n✅ Network Generation Complete!")
        print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
        print()
        
        print(f"📊 Network Statistics:")
        print(f"   • Total collections processed: {metadata['collections_analyzed']}")
        print(f"   • Successful nodes: {len(nodes)}")
        print(f"   • Network connections: {len(edges)}")
        print(f"   • Average connections per collection: {stats['avg_connections_per_collection']:.1f}")
        print(f"   • Network density: {(len(edges) / max(len(nodes) * (len(nodes) - 1) / 2, 1)) * 100:.2f}%")
        print()
        
        if nodes:
            # Analyze holder distribution
            holder_counts = [node['holders'] for node in nodes]
            total_holders = sum(holder_counts)
            avg_holders = total_holders / len(nodes)
            max_holders = max(holder_counts)
            min_holders = min(holder_counts)
            
            print(f"👥 Holder Analysis:")
            print(f"   • Total unique collections with holders: {len(nodes)}")
            print(f"   • Average holders per collection: {avg_holders:.1f}")
            print(f"   • Largest collection: {max_holders:,} holders")
            print(f"   • Smallest collection: {min_holders:,} holders")
            print()
            
            # Show top collections by holders
            nodes_by_holders = sorted(nodes, key=lambda x: x['holders'], reverse=True)
            print(f"🏆 Top 10 Collections by Holder Count:")
            for i, node in enumerate(nodes_by_holders[:10]):
                verified = "✅" if node['verified'] else "  "
                print(f"   {i+1:2d}. {verified} {node['name'][:40]:<40} - {node['holders']:,} holders")
            print()
            
            # Show top collections by network influence
            nodes_by_influence = sorted(nodes, key=lambda x: x['influence'], reverse=True)
            print(f"🌐 Top 10 Collections by Network Influence:")
            for i, node in enumerate(nodes_by_influence[:10]):
                verified = "✅" if node['verified'] else "  "
                print(f"   {i+1:2d}. {verified} {node['name'][:40]:<40} - {node['influence']} influence")
            print()
            
            # Show strongest connections
            if edges:
                edges_by_weight = sorted(edges, key=lambda x: x['weight'], reverse=True)
                print(f"🔗 Top 10 Strongest Connections:")
                for i, edge in enumerate(edges_by_weight[:10]):
                    source_name = next((n['name'] for n in nodes if n['id'] == edge['source']), 'Unknown')
                    target_name = next((n['name'] for n in nodes if n['id'] == edge['target']), 'Unknown')
                    print(f"   {i+1:2d}. {source_name[:25]:<25} ↔ {target_name[:25]:<25} ({edge['weight']} shared)")
                print()
        
        # Save the complete network data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save full network data
        full_filename = f"monad_nft_network_full_{timestamp}.json"
        with open(full_filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        # Save summary report
        summary = {
            "generation_info": {
                "timestamp": datetime.now().isoformat(),
                "generation_time_minutes": elapsed / 60,
                "collections_requested": limit,
                "min_shared_holders_threshold": min_shared_holders
            },
            "network_stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "avg_connections_per_collection": stats['avg_connections_per_collection'],
                "network_density_percent": (len(edges) / max(len(nodes) * (len(nodes) - 1) / 2, 1)) * 100
            },
            "holder_stats": {
                "total_collections_with_holders": len(nodes),
                "average_holders_per_collection": avg_holders if nodes else 0,
                "max_holders": max_holders if nodes else 0,
                "min_holders": min_holders if nodes else 0
            },
            "top_collections": [
                {
                    "rank": i + 1,
                    "name": node['name'],
                    "holders": node['holders'],
                    "influence": node['influence'],
                    "verified": node['verified']
                }
                for i, node in enumerate(nodes_by_holders[:20])
            ] if nodes else []
        }
        
        summary_filename = f"monad_nft_network_summary_{timestamp}.json"
        with open(summary_filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Also save as latest files for the web interface
        with open('monad_nft_network_latest.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"💾 Files Created:")
        print(f"   • {full_filename} - Complete network data")
        print(f"   • {summary_filename} - Summary report")
        print(f"   • monad_nft_network_latest.json - Latest data for web interface")
        print()
        
        print(f"🎯 Network generation complete! Ready for visualization.")
        print(f"📊 The network shows real holder relationships across {len(nodes)} NFT collections.")
        
    except Exception as e:
        print(f"❌ Error during network generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(generate_full_network()) 