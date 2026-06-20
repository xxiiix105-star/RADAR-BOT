from Shaheen.db.pg_store import SyncCollection

_anitcdb = SyncCollection("ANTICHANNEL")

async def is_antichnl(group_id):
    data = _anitcdb.find_one({"group_id": group_id})
    if not data:
        return False, None
    return True, data["mode"]

async def antichnl_on(group_id, mode):
    data = {"group_id": group_id, "mode": mode}
    existing = _anitcdb.find_one({"group_id": group_id})
    if existing:
        _anitcdb.update_one({"group_id": group_id}, {"$set": data})
    else:
        _anitcdb.insert_one(data)

def antichnl_off(group_id):
    stark = _anitcdb.find_one({"group_id": group_id})
    if not stark:
        return False
    _anitcdb.delete_one({"group_id": group_id})
    return True
