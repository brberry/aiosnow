import asyncio

from aiosnow import Client, fields, select
from aiosnow.custom_basemodel import CustomBaseModel
from aiosnow.custom_utils import query_date


class UserModel(CustomBaseModel):
    sys_id = fields.String(is_primary=True)
    user_name = fields.String()
    email = fields.String()


class SysEventModel(CustomBaseModel):
    sys_id = fields.String(is_primary=True)
    claimed_by = fields.String()
    descriptive_name = fields.String()
    instance = fields.String()
    name = fields.String()
    param1 = fields.String()
    param2 = fields.String()
    processed = fields.DateTime()
    processing_duration = fields.Integer()
    process_on = fields.DateTime()
    queue = fields.String()
    # rollback_context_id	Rollback context ID	Reference
    state = fields.String()
    table = fields.String()
    uri = fields.String()
    sys_created_by = fields.String()
    sys_created_on = fields.DateTime()
    sys_updated_by = fields.String()
    sys_updated_on = fields.DateTime()

instance_url = "nistsandbox2.servicenowservices.com"

oauth = {
    "client_id": "eeb277a2535ac250ec7390a3d1f2b062",
    "key_file": "C:/keys/snow/psd_connector_dev.key",
    "key_passphrase": 'f?MR/aizYlDvCi;"Kx2C',
    "subject": "splunk_sys"
}


async def main() -> None:
    client = Client(address=instance_url, oauth=oauth)

    # async with UserModel(client, table_name="sys_user") as user:
    #     response = await user.get_one(UserModel.user_name == "brb5150")
    #     print("({sys_id}): {user_name}".format(**response.data))
    #
    #     response = await user.get_one(UserModel.user_name == "brberry")
    #     print("({sys_id}): {user_name} {email}".format(**response.data))
    date_str = "2024-05-28 13:00:00"
    query_dt = query_date(date_str)

    query = select(
        SysEventModel.sys_created_on.after(query_dt)
    ).order_asc(SysEventModel.sys_created_on)

    async with SysEventModel(client, table_name="sysevent") as api:
        offset = 0
        rec_cnt = 0
        batch_cnt = 0
        limit = 5000
        while True:
            batch_cnt = 0
            for response in await api.get(query, limit=limit, offset=offset):
                rec_cnt += 1
                batch_cnt += 1
            offset += batch_cnt
            print(f"Retrieved {rec_cnt} records so far")
            if batch_cnt < limit:
                break
        print(f"Retrieved {rec_cnt} records in total")

    # async with SysEventModel(client, table_name="sysevent") as sys_event:
    #     response = await sys_event.get_one(UserModel.user_name == "brb5150")
    #     print(**response.data)


if __name__ == "__main__":
    asyncio.run(main(), debug=False)
