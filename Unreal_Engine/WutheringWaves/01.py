import re
import os
import json
import struct
import sqlite3
import argparse
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, default=r"D:\Reverse\_Unreal Engine\FModel\Output\Exports\Client\Content\Aki\ConfigDB")
    return parser.parse_args(args=args, namespace=namespace)

def table_to_dict(db_path, table_name):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result

def parse_bin_data(data):
    start_index = data.find(b'[{')
    end_index = data.rfind(b'}]')
    if start_index != -1 and end_index != -1:
        cleaned_data = data[start_index:end_index+2]
        return cleaned_data
    return None

def parse_flowstate(root):
    db_path = os.path.join(root, "db_flowState.db")
    flowstate_data = table_to_dict(db_path, "flowState")
    result = []
    scene = 0
    line = 0
    for item in flowstate_data:
        flow = parse_bin_data(item['BinData'])
        flow = json.loads(flow.decode('utf-8'))
        for flow_item in flow:
            if flow_item['Name'] == 'ShowTalk':
                flow_item_params = flow_item['Params']
                if flow_item_params.get('TalkSequence'):
                    print(f"Warning: Unexpected number of parameters in flow item: {flow_item_params}")
                    continue
                for flow_item_params_talk_items in flow_item_params['TalkItems']:
                    if flow_item_params_talk_items['Type'] == 'Talk':
                        WhoId = flow_item_params_talk_items['WhoId']
                        TextId = flow_item_params_talk_items['TextId']
                        TidTalk = flow_item_params_talk_items['TidTalk']
                    elif flow_item_params_talk_items['Type'] == 'Center':
                        WhoId = -1
                        TextId = flow_item_params_talk_items['TextId']
                        TidTalk = None
                    result.append({'WhoId': WhoId, 'TidTalk': TidTalk, 'Scene': scene, 'Line': line})
                    line += 1
        scene += 1

    return result

if __name__ == "__main__":
    args = parse_args()
    flowstate_data = parse_flowstate(args.root)
    pass