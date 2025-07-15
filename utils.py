import json
from functools import reduce

def get_market_index(question_id: str) -> int:
    return int(question_id[-2:], 16)

def get_index_set(question_ids: list[str]) -> int:
    indices = [get_market_index(id) for id in question_ids]
    return reduce(lambda acc, index: acc + (1 << index), set(indices), 0)

def load_abi(name: str):
    with open(f'D:/makebet/py_safe/abis/{name}.json', 'r') as f:
        return json.load(f)