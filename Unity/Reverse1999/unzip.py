import gzip

with gzip.open(r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\configs\allmanifest.dat", "rb") as f:
    data = f.read()
    
with open(r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\configs\allmanifest.bin", "wb") as f:
    f.write(data)