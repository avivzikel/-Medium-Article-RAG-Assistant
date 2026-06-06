import argparse
import json

from app.config import settings
from app.rag.retrieval import retrieve_context


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Test retrieval quality')
    parser.add_argument('--question', required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    contexts = retrieve_context(args.question, top_k=settings.top_k)
    print(json.dumps(contexts, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
