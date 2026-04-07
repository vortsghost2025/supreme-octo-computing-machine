import time
import requests

# Test different context lengths
ctx_lengths = [2048, 4096, 8192]
model = 'mistral:7b'
prompt = 'Count from 1 to 50.'

results = []

for ctx in ctx_lengths:
    start = time.time()
    r = requests.post('http://localhost:11434/api/generate', 
        json={'model': model, 'prompt': prompt, 'options': {'num_ctx': ctx}, 'stream': False})
    elapsed = time.time() - start
    
    data = r.json()
    tokens = data.get('eval_count', 0)
    duration = data.get('eval_duration', 0) / 1e9
    tps = tokens / duration if duration > 0 else 0
    
    results.append({'ctx': ctx, 'tokens': tokens, 'time': round(elapsed, 2), 'tps': round(tps, 2)})
    print(f"ctx={ctx}: {tokens} tokens in {elapsed:.2f}s = {tps:.2f} t/s")

print()
print('CONTEXT LENGTH BENCHMARK:')
for r in results:
    print(f"  {r['ctx']} ctx: {r['tps']} tokens/sec")