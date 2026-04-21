from openai import OpenAI

client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key="o3p08P2UaVz9g2CRUe8R1ApyZJSalOBr"
)

resp = client.chat.completions.create(
    model="mistral-small-latest",
    messages=[{"role": "user", "content": "Réponds juste: OK"}]
)
print(resp.choices[0].message.content)