# HALO-change-image-location

Python/GraphQL script for changing image file paths in [HALO](https://indicalab.com/halo/)

Loads a CSV file containing incorrect file paths for images in a HALO server and uses the HALO GraphQL API to update these file paths.

Key assumptions:
  1. All images live on a Windows machine (either on the HALO server itself or on a remote SMB storage server)
  2. No images have been deleted; they have just been renamed and/or moved into different folders
  3. A single SQL query is insufficient for fixing the broken file paths (i.e. more than a high-level folder was renamed)

If these 3 assumptions are true for you, read on.

This script is intended to be used by IT staff or tech-savvy researchers. **Use with caution!** Start with a small number of images/paths first, then scale up once you can confirm the script works for you.

# How to use

## 1. Create a HALO GraphQL service client

1. On the HALO machine, run these commands using an administrator shell:

```
cd "C:\Program Files\Indica Labs\Identity Provider"

.\IndicaLabs.ApplicationLayer.Halo.IdentityProvider.exe reconfigure --script AddResearchServiceClient "client_type=python;scopes=serviceuser|graphql"
```

2. Open the HALO Identity Provider configuration file at `C:\ProgramData\Indica Labs\Configuration\IndicaLabs.ApplicationLayer.Halo.IdentityProvider\local-production.yml`, find the client that you just created, and note down its full client ID and client secret.

Please read [the Indica Labs README](https://gitlab.com/indica_labs_public/example-code#step-2-create-halo-service-client) for more information about creating a client.

## 2. Set up local script environment

Ensure that Python is installed on your PC and its version is at least **3.12.9**.

Clone this git repository and place it somewhere on your computer. If you downloaded the repository as a ZIP, please extract the contents of the ZIP folder.

Create a file in the root of the repository named `secrets.json` and populate it with your HALO server's hostname and client details (the same client that you created above). This is _very_ sensitive data, so please ensure that `secrets.json` is only accessible to qualified lab or IT staff.

```json
{
    "hostname": "halo.bowser.example.org",
    "client_id": "python_BOWSER-HALO",
    "client_secret": "abc123def456=="
}
```

This script is intended to be ran on a separate PC and _not_ on the HALO server itself. If your HALO server has an FQDN and a valid certificate, please install that certificate on your machine now:
* Get an up-to-date .cer file for your HALO server's name
* Double-click .cer to install certificate
* Select **Install certificate**
* Store Location: **Local Machine**
* Select **Place all certificates in the following store** and select **Trusted Root Certification Authorities**

The script _may_ work if a raw IP address is provided to the `hostname` field, but you will probably have to fiddle with SSL settings in `main.py:create_client_session()` and `main.py:request_access_token()`.

Run `setup.bat` to create and prepare a virtual environment for the script.

### Input CSV file

The input CSV file is critical to the operation of the script, as it creates a 1:1 mapping of old/incorrect file paths to new/correct file paths for each HALO image.

Create a CSV file named `input.csv` in the repository's root. It should look like this:

| old_path | new_path |
| -------- | -------- |
| `\\1.2.3.4\lab_bowser\scans\Scan001.scn` | `\\1.2.3.4\lab_bowser\waluigi\updated_folder\Scan001.scn` |
| `\\1.2.3.4\lab_bowser\scans\Scan002.scn` | `\\1.2.3.4\lab_bowser\waluigi\addl_folder\Scan002.scn` |

Researchers will have to populate this spreadsheet manually to match the images' old incorrect paths to correct paths.

Note the amount of backslashes in the paths above (starts with `\\`; paths separated by a single `\`). Do not add additional backslashes or escape characters.

If you have access to your images' `pk` values, those can added into the CSV file as well:

| pk | old_path | new_path |
| -- | -------- | -------- |
| 81 | `\\1.2.3.4\lab_bowser\scans\Scan001.scn` | `\\1.2.3.4\lab_bowser\waluigi\updated_folder\Scan001.scn` |
| 82 | `\\1.2.3.4\lab_bowser\scans\Scan002.scn` | `\\1.2.3.4\lab_bowser\waluigi\addl_folder\Scan002.scn` |

If `pk` is provided, then `pk` will be used to query for images' unique IDs. If `pk` is absent, then the script will attempt to query for image IDs using `old_path`.

## 3. Run the script

Activate the virtual environment and run the script:

```
# Can alternatively use ".ps1" script if using PowerShell on Windows
.\.venv\Scripts\Activate.bat

python main.py
```

# Extra links

* "Italo", an alternative tool by Christian Rickert at University of Colorado: https://github.com/rickert-lab/Italo/tree/main
* Indica Labs Python and GraphQL example code: https://gitlab.com/indica_labs_public/example-code
* If your lab/institute has a [HALO Link](https://indicalab.com/halo-link/) web server, visit its GraphQL workbench at the "/graphql" endpoint to quickly test GraphQL queries: https://halo.bowser.example.org/graphql
* `gql` Python package documentation: https://gql.readthedocs.io/en/stable/
* `truststore` Python package documentation (use system certificate stores): https://truststore.readthedocs.io/en/latest/
