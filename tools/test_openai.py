from openai import OpenAI

client = OpenAI()
resp = client.responses.create(
    model="gpt-5-mini",
    input="What is capital of France?"
)
print(resp.output_text)
