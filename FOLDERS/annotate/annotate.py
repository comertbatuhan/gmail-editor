import json
from openai import OpenAI
from pathlib import Path
from prompts import SYSTEM_PROMPT
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR   = ROOT_DIR / "data"


def load_api_key(keyfile_path: Path = CONFIG_DIR / "keys.json"):
    with open(keyfile_path) as f:
        return json.load(f)["OPENAI_API_KEY"]


def load_raw_emails(input_path: Path):
    with open(input_path, encoding="utf-8") as f:
        return json.load(f)


def save_annotated_emails(data, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def chunk(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]


client = OpenAI(api_key=load_api_key("config/keys.json"))
def annotate_batch(batch, model="gpt-4o-mini", client=client):       

    user_message = json.dumps(batch, ensure_ascii=False)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        response_format={"type": "json_object"}          
    )

    return json.loads(response.choices[0].message.content)


def annotate_all(input_path, output_path, batch_size=100):
    emails = load_raw_emails(input_path)[0]
    annotated = []

    for batch in chunk(emails, batch_size):
        try:
            labels = annotate_batch(batch)
            annotated.extend(labels)
        except Exception as e:
            print(f"Error on batch starting with ID {batch[0]['id']}: {e}")

    save_annotated_emails(annotated, output_path)


if __name__ == "__main__":
    annotate_all(
        input_path=DATA_DIR / "raw_emails.json",
        output_path=DATA_DIR / "labeled_emails.json",
        batch_size=1,
    )
