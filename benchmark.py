import time
import requests

models = ['llama3:8b', 'mistral:7b']
prompt = 'Write a detailed explanation of how neural networks work, covering backpropagation, gradients, and optimization. Include examples.'

results = []

for model in models:
    # Warm up
    requests.post('http://localhost:11434/api/generate', json={'model': model, 'prompt': 'hi', 'stream': False})
    
    # Benchmark
    start = time.time()
    r = requests.post('http://localhost:11434/api/generate', json={'model': model, 'prompt': prompt, 'stream': False})
    elapsed = time.time() - start
    
    data = r.json()
    tokens = data.get('eval_count', 0)
    duration = data.get('eval_duration', 0) / 1e9
    
    tps = tokens / duration if duration > 0 else 0
    
    results.append({
        'model': model,
        'total_time': round(elapsed, 2),
        'tokens': tokens,
        'duration_sec': round(duration, 2),
        'tokens_per_sec': round(tps, 2)
    })
    print(f'{model}: {tokens} tokens in {elapsed:.2f}s = {tps:.2f} t/s')

print()
print('='*50)
print('RESULTS:')
for r in results:
    print(f"{r['model']}: {r['tokens_per_sec']} tokens/sec")