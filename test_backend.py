from flask import Flask, Response
import json
import time
import random
from datetime import datetime
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)

def generate_transaction():
    """Generate a random transaction"""
    value = random.uniform(0.1, 2000)  # Random value between 0.1 and 2000 MON
    return {
        "hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
        "value": str(value)
    }

def generate_cityscape_data():
    """Generate artificial cityscape data"""
    while True:
        # Generate between 1 to 5 transactions
        transactions = [generate_transaction() for _ in range(random.randint(1, 5))]
        
        data = {
            "tps": random.uniform(100, 8000),
            "latest_block": {
                "number": random.randint(1000000, 9999999)
            },
            "total_fees_in_batch": random.uniform(0.1, 10),
            "transactions": transactions
        }
        
        yield f"data: {json.dumps(data)}\n\n"
        time.sleep(0.5)  # Send data every 500ms

def generate_derby_data():
    """Generate artificial derby racing data"""
    racers = {
        "LFJ": ["0x45A62B090DF48243F12A21897e7ed91863E2c86b"],
        "PancakeSwap": ["0x94D220C58A23AE0c2eE29344b00A30D1c2d9F1bc"],
        "Bean Exchange": ["0xCa810D095e90Daae6e867c19DF6D9A8C56db2c89"],
        "Ambient Finance": ["0x88B96aF200c8a9c35442C8AC6cd3D22695AaE4F0"],
        "Izumi Finance": ["0xf6ffe4f3fdc8bbb7f70ffd48e61f17d1e343ddfd"],
        "Octoswap": ["0xb6091233aAcACbA45225a2B2121BBaC807aF4255"],
        "Uniswap": ["0x3aE6D8A282D67893e17AA70ebFFb33EE5aa65893"]
    }
    
    while True:
        data = {name: {"tps": random.uniform(100, 8000)} for name in racers.keys()}
        yield f"data: {json.dumps(data)}\n\n"
        time.sleep(1)  # Send data every second

@app.route('/firehose-stream')
def firehose_stream():
    return Response(
        generate_cityscape_data(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

@app.route('/derby-stream')
def derby_stream():
    return Response(
        generate_derby_data(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True) 