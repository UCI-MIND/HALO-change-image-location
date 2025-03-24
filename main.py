import asyncio
import csv
import json
import ssl
from pathlib import Path

import aiohttp
import truststore
from gql import Client
from gql.transport.websockets import WebsocketsTransport

import queries

CSV_FILE_NAME = "input.csv"
SECRETS_FILE_NAME = "secrets.json"

with open(Path(Path(__file__).parent, SECRETS_FILE_NAME)) as infile:
    secrets = json.load(infile)
HOSTNAME = secrets["hostname"]
CLIENT_ID = secrets["client_id"]
CLIENT_SECRET = secrets["client_secret"]

# This bool is changed based on the contents of the input CSV; do not touch!
PK_IN_INPUT = True


def load_csv_data(csv_filename: str) -> list[dict]:
    global PK_IN_INPUT
    result = []
    with open(Path(Path(__file__).parent, csv_filename)) as infile:
        reader = csv.DictReader(infile)

        # Confirm CSV headers
        headers = reader.fieldnames
        if "old_path" not in headers or "new_path" not in headers:
            print(
                "Headers 'old_path' and 'new_path' must be present in the input CSV. This script saw:"
            )
            print(headers)
            exit(1)
        if "pk" not in headers:
            print("No 'pk' column found in input CSV, will query for imageId with location")
            PK_IN_INPUT = False
        else:
            print("'pk' column found in input CSV, will query for imageId with pk")

        # Load the data
        for row in reader:
            sanitized_row = dict()
            if "pk" in row:
                sanitized_row["pk"] = int(row["pk"])
            # 2 ways to work with backslashes in Windows file paths as strings in Python:
            # 1. Provide the path as a string literal (string prefixed with 'r'). Example:
            #       r"\\1.2.3.4\lab_bowser\scans\Scan001.scn"
            # 2. Double each backslash to escape the escape sequence. Example:
            #       "\\\\1.2.3.4\\lab_bowser\\scans\\Scan001.scn"
            # You may have to sanitize the paths in your CSV ahead of time to ensure that
            # the paths are loaded correctly here.
            sanitized_row["old_path"] = rf"{row['old_path']}".strip()
            sanitized_row["new_path"] = rf"{row['new_path']}".strip()
            result.append(sanitized_row)

    # Check for duplicate paths in new_path column (via https://stackoverflow.com/a/9835819)
    seen = set()
    dupes = []
    for row in result:
        if row["new_path"] in seen:
            dupes.append(row["new_path"])
        else:
            seen.add(row["new_path"])
    if len(dupes) > 0:
        print(f"Found {len(dupes)} duplicate path(s) in new_path column:")
        print(dupes)
        print("Please remove or correct all duplicate paths to run this script.")
        exit(1)
    return result


async def request_access_token() -> str:
    async with aiohttp.ClientSession() as session:
        # Use system certificate stores to contact HALO server
        # You should have already installed the HALO Link server certificate on your machine!
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        async with session.request(
            method="post",
            url=f"https://{HOSTNAME}/idsrv/connect/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "scope": "serviceuser graphql",
                "grant_type": "client_credentials",
            },
            ssl=ctx,
            raise_for_status=True,
        ) as response:
            data = await response.json()
        return data["access_token"]


async def create_client_session(token: str, add_local_bearer=False):
    ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    transport = WebsocketsTransport(
        url=f"wss://{HOSTNAME}/graphql",
        headers={"authorization": f"bearer {token}"},
        subprotocols=[WebsocketsTransport.APOLLO_SUBPROTOCOL],
        ssl=ctx,
    )
    if add_local_bearer:
        transport.headers["x-authentication-scheme"] = "LocalBearer"

    client = Client(transport=transport)
    return await client.connect_async()


async def get_image_id_via_pk(session, pk: str) -> str:
    params_imageByPk = {"pk": pk}
    result_imageByPk = await session.execute(
        queries.query_imageByPk, variable_values=params_imageByPk
    )
    return result_imageByPk["imageByPk"]["id"]


async def get_image_id_via_location(session, location: str) -> str:
    params_imagesByLocation = {"location": location}
    result_imagesByLocation = await session.execute(
        queries.query_imagesByLocation, variable_values=params_imagesByLocation
    )
    found_images = result_imagesByLocation["imagesByLocation"]
    if len(found_images) == 1:
        return found_images[0]["id"]
    return ""


async def change_image_path(session, img_id: str, new_path: str) -> str:
    params_changeImageLocation = {
        "input": {
            "imageId": img_id,
            "newLocation": new_path,
        }
    }
    result_changeImageLocation = await session.execute(
        queries.mutation_changeImageLocation, variable_values=params_changeImageLocation
    )
    if result_changeImageLocation["changeImageLocation"]["failed"] is None:
        return result_changeImageLocation["changeImageLocation"]["mutated"][0]["node"]["location"]
    return ""


async def run_queries(session, local_data: list[dict]) -> None:
    for row in local_data:
        if PK_IN_INPUT:
            pk = row["pk"]
        halo_image_path = row["old_path"]
        updated_path = row["new_path"]

        if PK_IN_INPUT:
            print(f"Processing image [pk {pk}]:")
            image_id = await get_image_id_via_pk(session, pk)
        else:
            print(f"Processing image [{halo_image_path}]:")
            image_id = await get_image_id_via_location(session, halo_image_path)
        if image_id:
            print(f"* Got imageId {image_id}")
            updated_path_from_api = await change_image_path(session, image_id, updated_path)
            if updated_path_from_api:
                print(f'* Changed from "{halo_image_path}" to "{updated_path_from_api}"')
    return


async def main() -> None:
    csv_data = load_csv_data(CSV_FILE_NAME)
    token = await request_access_token()
    session = await create_client_session(token)
    await run_queries(session, csv_data)
    await session.client.close_async()
    return


if __name__ == "__main__":
    asyncio.run(main())
