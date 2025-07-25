from lib.utils import get_dir_location
import xml.etree.ElementTree as ET
from .mappings import Mappings
import requests
import json
import os

# make sure the cache directory exists
print("Making __cache__")
if not os.path.exists(get_dir_location("__cache__")):
    print("Made __cache__ directory.", get_dir_location("__cache__"))
    os.mkdir(get_dir_location("__cache__"))


def get_burger():
    if not os.path.exists(get_dir_location("__cache__/Burger")):
        print("\033[92mDownloading Burger...\033[m")
        os.system(
            f"cd {get_dir_location('__cache__')} && git clone https://github.com/mat-1/Burger && cd Burger && git pull"
        )

        print("\033[92mInstalling dependencies...\033[m")
        os.system(
            f"cd {get_dir_location('__cache__')}/Burger && python -m venv venv && venv/bin/pip install six jawa"
        )


def get_pumpkin_extractor():
    if not os.path.exists(get_dir_location("__cache__/pumpkin-extractor")):
        print("\033[92mDownloading Pumpkin-MC/Extractor...\033[m")
        os.system(
            f"cd {get_dir_location('__cache__')} && git clone https://github.com/Pumpkin-MC/Extractor pumpkin-extractor && cd pumpkin-extractor && git pull"
        )

    return get_dir_location("__cache__/pumpkin-extractor")


def get_version_manifest():
    if not os.path.exists(get_dir_location("__cache__/version_manifest.json")):
        print("\033[92mDownloading version manifest...\033[m")
        version_manifest_data = requests.get(
            "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
        ).json()
        with open(get_dir_location("__cache__/version_manifest.json"), "w") as f:
            json.dump(version_manifest_data, f)
    else:
        with open(get_dir_location("__cache__/version_manifest.json"), "r") as f:
            version_manifest_data = json.load(f)
    return version_manifest_data


def get_version_data(version_id: str):
    if not os.path.exists(get_dir_location(f"__cache__/{version_id}.json")):
        version_manifest_data = get_version_manifest()

        print(f"\033[92mGetting data for \033[1m{version_id}..\033[m")
        try:
            package_url = next(
                filter(
                    lambda v: v["id"] == version_id, version_manifest_data["versions"]
                )
            )["url"]
        except StopIteration:
            raise ValueError(
                f"No version with id {version_id} found. Maybe delete __cache__/version_manifest.json and try again?"
            )
        package_data = requests.get(package_url).json()
        with open(get_dir_location(f"__cache__/{version_id}.json"), "w") as f:
            json.dump(package_data, f)
    else:
        with open(get_dir_location(f"__cache__/{version_id}.json"), "r") as f:
            package_data = json.load(f)
    return package_data


def get_client_jar(version_id: str):
    if not os.path.exists(get_dir_location(f"__cache__/client-{version_id}.jar")):
        package_data = get_version_data(version_id)
        print("\033[92mDownloading client jar...\033[m")
        client_jar_url = package_data["downloads"]["client"]["url"]
        with open(get_dir_location(f"__cache__/client-{version_id}.jar"), "wb") as f:
            f.write(requests.get(client_jar_url).content)


def get_server_jar(version_id: str):
    if not os.path.exists(get_dir_location(f"__cache__/server-{version_id}.jar")):
        package_data = get_version_data(version_id)
        print("\033[92mDownloading server jar...\033[m")
        server_jar_url = package_data["downloads"]["server"]["url"]
        with open(get_dir_location(f"__cache__/server-{version_id}.jar"), "wb") as f:
            f.write(requests.get(server_jar_url).content)


def get_mappings_for_version(version_id: str):
    if not os.path.exists(get_dir_location(f"__cache__/mappings-{version_id}.txt")):
        package_data = get_version_data(version_id)

        client_mappings_url = package_data["downloads"]["client_mappings"]["url"]

        mappings_text = requests.get(client_mappings_url).text

        with open(get_dir_location(f"__cache__/mappings-{version_id}.txt"), "w") as f:
            f.write(mappings_text)
    else:
        with open(get_dir_location(f"__cache__/mappings-{version_id}.txt"), "r") as f:
            mappings_text = f.read()
    return Mappings.parse(mappings_text)


def get_fabric_data(version_id: str):
    # https://meta.fabricmc.net/v2/versions/yarn
    path = get_dir_location(f"__cache__/fabric-{version_id}.json")

    if not os.path.exists(path):
        print(f"\033[92mDownloading Fabric metadata for {version_id}...\033[m")
        url = f"https://meta.fabricmc.net/v1/versions/loader/{version_id}"
        yarn_versions_data = requests.get(url).json()
        with open(path, "w") as f:
            json.dump(yarn_versions_data, f)
    else:
        with open(path, "r") as f:
            yarn_versions_data = json.load(f)
    return yarn_versions_data


def get_latest_fabric_api_version():
    path = get_dir_location("__cache__/fabric-api-maven-metadata.xml")

    if not os.path.exists(path):
        print("\033[92mDownloading Fabric API metadata...\033[m")
        url = "https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml"
        maven_metadata_xml = requests.get(url).text
        with open(path, "w") as f:
            json.dump(maven_metadata_xml, f)
    else:
        with open(path, "r") as f:
            maven_metadata_xml = json.load(f)

    tree = ET.ElementTree(ET.fromstring(maven_metadata_xml))
    return tree.find(".//latest").text


def get_fabric_api_versions():
    # https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml
    if not os.path.exists(get_dir_location("__cache__/fabric_api_versions.json")):
        print("\033[92mDownloading Fabric API versions...\033[m")
        fabric_api_versions_xml_text = requests.get(
            "https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml"
        ).text
        # parse xml
        fabric_api_versions_data_xml = ET.fromstring(fabric_api_versions_xml_text)
        fabric_api_versions = []

        versioning_el = fabric_api_versions_data_xml.find("versioning")
        assert versioning_el
        versions_el = versioning_el.find("versions")
        assert versions_el

        for version_el in versions_el.findall("version"):
            fabric_api_versions.append(version_el.text)

        with open(get_dir_location("__cache__/fabric_api_versions.json"), "w") as f:
            f.write(json.dumps(fabric_api_versions))
    else:
        with open(get_dir_location("__cache__/fabric_api_versions.json"), "r") as f:
            fabric_api_versions = json.loads(f.read())
    return fabric_api_versions


def get_fabric_loader_versions():
    # https://meta.fabricmc.net/v2/versions/loader
    if not os.path.exists(get_dir_location("__cache__/fabric_loader_versions.json")):
        print("\033[92mDownloading Fabric loader versions...\033[m")
        fabric_api_versions_json = requests.get(
            "https://meta.fabricmc.net/v2/versions/loader"
        ).json()

        fabric_api_versions = []
        for version in fabric_api_versions_json:
            fabric_api_versions.append(version["version"])

        with open(get_dir_location("__cache__/fabric_loader_versions.json"), "w") as f:
            f.write(json.dumps(fabric_api_versions))
    else:
        with open(get_dir_location("__cache__/fabric_loader_versions.json"), "r") as f:
            fabric_api_versions = json.loads(f.read())
    return fabric_api_versions


def clear_version_cache():
    print("\033[92mClearing version cache...\033[m")
    files = [
        "version_manifest.json",
        "yarn_versions.json",
        "fabric_api_versions.json",
        "fabric_loader_versions.json",
        "fabric-api-maven-metadata.xml",
    ]
    for file in files:
        if os.path.exists(get_dir_location(f"__cache__/{file}")):
            os.remove(get_dir_location(f"__cache__/{file}"))

    burger_path = get_dir_location("__cache__/Burger")
    if os.path.exists(burger_path):
        os.system(f"cd {burger_path} && git pull")
    pumpkin_path = get_dir_location("__cache__/pumpkin-extractor")
    if os.path.exists(pumpkin_path):
        os.system(
            f"cd {pumpkin_path} && git add . && git stash && git pull && git stash pop && git checkout HEAD -- src/main/resources/fabric.mod.json"
        )
