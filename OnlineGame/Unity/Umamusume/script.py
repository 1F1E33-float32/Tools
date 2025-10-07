import UnityPy

env = UnityPy.load(r"/mnt/e/OnlineGame_Dataset/Umamusume/RAW/story/data/00/0000/storytimeline_000000001")

objects = env.objects

for obj in objects:
    if obj.type.name == "MonoBehaviour":
        mono_tree = obj.read_typetree()
        pass