from pgstore import SyncCollection

anitcdb = SyncCollection("ANTICHANNEL")


async def is_antichnl(group_id):
    data = anitcdb.find_one({"group_id": group_id})
    if not data:
        return False, None
    return True, data["mode"]


async def antichnl_on(group_id, mode):
    try:
        anitcdb.update_one(
            {"group_id": group_id},
            {"$set": {"group_id": group_id, "mode": mode}},
            upsert=True,
        )
    except Exception:
        return


def antichnl_off(group_id):
    stark = anitcdb.find_one({"group_id": group_id})
    if not stark:
        return False
    anitcdb.delete_one({"group_id": group_id})
    return True
