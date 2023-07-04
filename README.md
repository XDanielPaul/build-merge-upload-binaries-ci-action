# build-merge-upload-binaries-ci-action
This Github Action builds merged binaries of ESP projects and uploads them to the Github pages.

# Usage

## Step 1: Setup github pages in your repository
You will have to setup Github pages in your repository. The binaries will be uploaded to the `gh-pages` branch of your repository.
## Step 2: Configuration file
It is important to have `.idf_build_apps.toml` configuration file in the root directory of your repository. This file is used to configure the build process. 
For further information, please refer to the [documentation](https://docs.espressif.com/projects/idf-build-apps/en/latest/config_file.html).

Example configuration file:
```toml
paths = "examples" # Paths to search for buildable projects ["examples", "components"]
target = "all" # esp32, esp32s2, esp32c3, esp32s3, all...
recursive = true # Search for buildable projects recursively on the paths

# Configuration file for the build process 
config = "sdkconfig.defaults"

# Build related options
build_dir = "build_@w" # Build directory
```
**Do not overwrite** `--collect-app-info` **option!**

## Inputs
### `github_token`
**Required.** The Github token to use for uploading the binaries.

### `idf_version`
The version of the ESP-IDF to use for building the binaries.
**Default:** `"latest"`

## Step 3: You will have to run the action on a container with ESP-IDF installed. 
### Example usage

```yaml
jobs:

  build-and-upload-binaries:
    strategy:
      matrix:
        idf_ver: ["latest"]
    runs-on: ubuntu-latest
    container: espressif/idf:${{ matrix.idf_ver }}
    steps:
      - name: Checkout repo
        uses: actions/checkout@v3
        with:
          submodules: 'recursive'

      - name: Action for Building and Uploading Binaries
        uses: XDanielPaul/build-merge-upload-binaries-ci-action@v1.0
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          idf_version: ${{ matrix.idf_ver }}
```

## Step 4: Switch github pages to the `gh-pages` branch
After the action has finished, you will have to switch the Github pages to the `gh-pages` branch. You can do this in the settings of your repository.