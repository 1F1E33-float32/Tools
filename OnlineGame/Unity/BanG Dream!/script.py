import json
import argparse
from glob import glob

def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"E:\Game_Dataset\jp.co.craftegg.band\EXP\Story")
    parser.add_argument("--output", default=r"E:\Game_Dataset\jp.co.craftegg.band\EXP\index.json")
    return parser.parse_args()

def clean_text(text):
    text = text.replace("「", "").replace("」", "").replace("『", "").replace("』", "").replace("【", "").replace("】", "")
    text = text.replace("\\n", "\n").replace("\n", "").replace('\\"', '"')
    text = text.replace("\u3000", "")
    return text

def main():
    args = args_parser()
    root = args.root
    output = args.output

    filelist = glob(f"{root}/**/*.json", recursive=True)
    result = []
    for file in filelist:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            major = data.get("scenarioSceneId")
            if major is None:
                continue
            talkData = data["talkData"]
            for i in range(len(talkData)):
                Speaker = talkData[i]["windowDisplayName"]
                Text = talkData[i]["body"]
                Text = clean_text(Text)
                Voice = talkData[i]["voices"]
                if len(Voice) == 0:
                    continue
                else:
                    Voice = Voice[0]["voiceId"]
                result.append({"major": major, "minori": i, "Speaker": Speaker, "Voice": Voice, "Text": Text})
    
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(len(result))

if __name__ == "__main__":
    main()