# MaaGF2Exilium for Android

The Android APK packages this project's resources with the pinned
[MaaFwApp](https://github.com/Aliothmoon/MaaFwApp) frontend and the native
[MaaFramework](https://github.com/MaaXYZ/MaaFramework) engine. Android builds
download the latest MaaFramework release, matching the desktop workflow.
The desktop Python environment remains separate.

## GitHub Actions

**Build Android APK** builds a debug arm64-v8a APK for relevant pushes to
`main` / `master` and pull requests. Debug builds do not need signing secrets.
The workflow can also be run manually with `assemble: release` to produce signed
artifacts without publishing them:

- `MaaGF2Exilium-android-universal-<version>.apk` (arm64-v8a and x86_64)
- `MaaGF2Exilium-android-arm64-v8a-<version>.apk`
- `MaaGF2Exilium-android-x86_64-<version>.apk`

Before the first release tag after merging, repository maintainers must add
these four repository Actions Secrets under
**Settings > Secrets and variables > Actions > Secrets > New repository secret**:

| Secret | Value |
| --- | --- |
| `KEYSTORE_BASE64` | Single-line Base64 encoding of the private signing keystore |
| `KEYSTORE_PASSWORD` | Keystore password |
| `KEY_ALIAS` | Signing key alias (`maagf2exilium` for the prepared key) |
| `KEY_PASSWORD` | Signing key password |

Use a dedicated MaaGF2Exilium signing key. The intended certificate subject is
`CN=MaaGF2Exilium, OU=MaaGF2Exilium, O=MaaGF2Exilium, L=Unknown, ST=Unknown, C=Unknown`.
Signing material must be handed over privately. Keep the keystore, encoded
contents, passwords, and secrets JSON outside Git and the PR.
Back up the key securely and retain it for future APK updates.

Pushing a `v*` tag builds all three signed Android APKs alongside the desktop
packages and resource update. The existing release job waits for all builds to
succeed, then publishes their artifacts together in the same GitHub Release.
An Android build or signing failure stops the combined release publication.
Configure the four signing secrets and test a manual signed build before the
first release tag after merging. Existing MirrorChyan desktop/resource uploads
continue as before; Android updates use this repository's GitHub Releases.

## Versions and updates

Use SemVer tags such as `v2.7.3` or `v2.7.3-beta.1`. The same version is applied
to the APK and its packaged interface; tags with a prerelease suffix publish
GitHub prereleases for the Android beta update channel. Untagged builds resolve
to a valid development version, including repositories with no tags.

MaaFwApp derives Android `versionCode` from the full project commit count. Each
published APK must have a higher count than its predecessor, especially after a
rebase. A second tag on the same commit does not increase it. The build fetches
full history, and the version code also controls unpacking updated resources.

The application ID is `com.aliothmoon.maafw.maagf2exilium`, and the launcher name
is **MaaGF2Exilium**.

## Local build

Install JDK 25, Android SDK platform 37, NDK 29.0.13113456, CMake 3.22.1, and
Python 3.13 for the packaging scripts. The Android app supports Android 9 or newer.
The desktop project's Python environment remains separate.

From the project root:

```powershell
git submodule update --init --recursive
python -m unittest discover -s tests -p test_android_packaging.py -v
python scripts/prepare_android.py --version 0.0.0-dev --repository DarkLingYun/MaaGF2Exilium
```

Deploy the latest MaaFramework Android libraries from the frontend directory:

```powershell
cd Android/MaaFwApp
python scripts/setup_maa_framework.py --abi arm64-v8a
```

Create `Android/MaaFwApp/local.properties`:

```properties
sdk.dir=C:/path/to/Android/Sdk
pi.profile=../profile.yaml
build.debugAbi=arm64-v8a
build.ndkVersion=29.0.13113456
build.versionName=0.0.0-dev
```

Then build or install from `Android/MaaFwApp`:

```powershell
.\gradlew.bat :app:assembleDebug
# To install onto a connected Android device:
.\gradlew.bat :app:installDebug
```

Find the APK under `app/build/outputs/apk/debug/`. For a universal release,
also deploy `--abi x86_64`, set `build.releaseAbi=arm64-v8a,x86_64`, provide
`KEYSTORE_PATH`, `KEYSTORE_PASSWORD`, `KEY_ALIAS`, and `KEY_PASSWORD` in the
environment, and run `:app:assembleRelease`.

Use a SemVer `build.versionName`; a bare hash cannot be parsed by the updater.
Run `python scripts/android_version.py` from the project root to resolve it.
GitHub Actions supplies both the repository URL and version automatically, so
builds made in a fork use that fork's releases.

## Resources and device use

Rerun `prepare_android.py` after editing resources or translations.
`Android/assets/` is generated and ignored. The script stages the Chinese and
English Android packs, ppocr_v6 medium OCR models, and license. Resource paths
are relative to the installed PI directory; the desktop interface and resources
remain unchanged.

The package excludes the PC controller/resource pack and **Community daily
operations**, whose `CommunityDailyAction` callback is not implemented in the
project's agent. Other game tasks, server choices, and options are retained.
No Python runtime is bundled. Additional custom actions or recognition require
an Android agent runtime; packaging rejects unsupported callbacks.

Install the APK, allow notifications and required background permissions, and
connect Shizuku or root in the app. Choose the installed game server and resource
language. Pipelines assume a landscape 16:9 display; select a matching virtual
display preset when needed. Sign into the game manually before starting tasks.
Validate recognition and input on a physical device before unattended use.
