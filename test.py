import orjson

data = {"name": "Alice", "age": 30, "scores": [95, 87, 92]}

# Serialize to JSON bytes
json_bytes = orjson.dumps(data)

# Write to file
with open("data.json", "wb") as f:
    f.write(json_bytes)

