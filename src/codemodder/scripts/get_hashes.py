import sys

import requests


def get_package_hashes(package_name: str, version: str) -> list[str]:
    """
    Fetch the SHA256 hashes for a given package version from PyPI.
    """
    url = f"https://pypi.org/pypi/{package_name}/{version}/json"
    response = requests.get(url, timeout=60)
    hashes = []

    if response.status_code == 200:
        data = response.json()
        for release in data.get("urls", []):
            sha256 = release.get("digests", {}).get("sha256")
            if sha256:
                hashes.append(sha256)
    else:
        print(f"Failed to fetch data for {package_name}=={version}", file=sys.stderr)

    return hashes


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py package1==version package2==version")
        sys.exit(1)
    for arg in sys.argv[1:]:
        if "==" not in arg:
            print(
                f"Invalid format '{arg}'. Expected format: PackageName==Version",
                file=sys.stderr,
            )
            continue

        package_name, version = arg.split("==", 1)
        if hashes := get_package_hashes(package_name, version):
            print(f"SHA256 hashes for {package_name}=={version}:")
            for hash_value in hashes:
                print(hash_value)
        else:
            print(f"No hashes found for {package_name}=={version}")


if __name__ == "__main__":
    main()
