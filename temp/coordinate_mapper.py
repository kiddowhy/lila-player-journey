
import os,re,sys,json
import pandas as pd
import pyarrow.parquet as pq

MINIMAP_SIZE=1024
MAP_CONFIG={
"AmbroseValley":{"scale":900,"origin_x":-370,"origin_z":-473},
"GrandRift":{"scale":581,"origin_x":-290,"origin_z":-290},
"Lockdown":{"scale":1000,"origin_x":-500,"origin_z":-500},
}

def decode_events(df):
    if "event" in df.columns:
        df["event"]=df["event"].apply(lambda x:x.decode("utf-8") if isinstance(x,bytes) else x)
    return df

def classify_players(df):
    def c(uid):
        if uid is None or (isinstance(uid,float) and pd.isna(uid)): return "Unknown"
        if isinstance(uid,bytes): uid=uid.decode("utf-8")
        uid=str(uid).strip()
        if uid=="": return "Unknown"
        return "Bot" if re.fullmatch(r"\d+",uid) else "Human"
    df["player_type"]=df["user_id"].apply(c)
    return df

def load_day(folder):
    frames=[]
    for file in sorted(os.listdir(folder)):
        p=os.path.join(folder,file)
        if not os.path.isfile(p): continue
        try:
            d=pq.read_table(p).to_pandas()
            frames.append(classify_players(decode_events(d)))
        except Exception:
            pass
    if not frames: raise RuntimeError("No telemetry found")
    return pd.concat(frames,ignore_index=True)

def world_to_minimap(map_id,x,z):
    cfg=MAP_CONFIG.get(map_id)
    if cfg is None: return None,None
    u=(x-cfg["origin_x"])/cfg["scale"]
    v=(z-cfg["origin_z"])/cfg["scale"]
    px=max(0,min(MINIMAP_SIZE,u*MINIMAP_SIZE))
    py=max(0,min(MINIMAP_SIZE,(1-v)*MINIMAP_SIZE))
    return round(px,2),round(py,2)

def add_coords(df):
    vals=df.apply(lambda r: world_to_minimap(r["map_id"],r["x"],r["z"]),axis=1)
    df["pixel_x"]=[v[0] for v in vals]
    df["pixel_y"]=[v[1] for v in vals]
    return df

def export_json(df,name):
    out=[]
    for _,r in df.iterrows():
        out.append({
            "user_id":r["user_id"],"player_type":r["player_type"],
            "match_id":r["match_id"],"map_id":r["map_id"],
            "event":r["event"],"timestamp":str(r["ts"]),
            "world_x":float(r["x"]),"world_y":float(r["y"]),"world_z":float(r["z"]),
            "pixel_x":None if pd.isna(r["pixel_x"]) else float(r["pixel_x"]),
            "pixel_y":None if pd.isna(r["pixel_y"]) else float(r["pixel_y"])
        })
    with open(name,"w",encoding="utf-8") as f: json.dump(out,f,indent=2)

def main():
    folder=sys.argv[1] if len(sys.argv)>1 else "player_data/February_10"
    print("Loading",folder)
    df=add_coords(load_day(folder))
    print(df[["map_id","user_id","player_type","event","x","z","pixel_x","pixel_y"]].head(30))
    df.to_csv("telemetry_with_minimap_coordinates.csv",index=False)
    export_json(df,"telemetry_with_minimap_coordinates.json")
    print("Done")

if __name__=="__main__":
    main()
