import httpx
from openai import AsyncOpenAI

class ClientManager:
    def __init__(self):
        self.clients = {}

    def get_client(self, config):
        api_provider = config['api_provider']
        base_url = config['base_url']
        api_key = config['api_key']
        proxy_on = config.get('proxy_on', False)
        
        key = f"{api_provider}-{base_url}-{api_key}"
        
        if proxy_on:
            proxy = config.get('proxy', None)
            key += f"-{proxy}"
            if key not in self.clients:
                http_client = httpx.AsyncClient(proxies={
                    "http://": proxy,
                    "https://": proxy
                })
                self.clients[key] = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    http_client=http_client
                )
        else:
            if key not in self.clients:
                self.clients[key] = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
        
        return self.clients[key]
