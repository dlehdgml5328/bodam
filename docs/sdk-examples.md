# API SDK 코드 예시

## JavaScript
```ts
import axios from 'axios';

const client = axios.create({ baseURL: 'https://api.bodam.example', withCredentials: true });

export async function listDonations() {
  const { data } = await client.get('/donations');
  return data;
}
```

## Python
```python
import httpx

client = httpx.AsyncClient(base_url="https://api.bodam.example", timeout=5)

async def list_donations():
    response = await client.get("/donations")
    response.raise_for_status()
    return response.json()
```
