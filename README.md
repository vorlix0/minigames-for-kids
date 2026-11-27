# Minigames for Kids

A collection of simple minigames written in Python. The first game is a maze.

## Getting Started

Python 3.8 or newer with Tkinter is required. From the project directory, run:

```powershell
py main.py
```

On systems where Python is available as `python3`, you can run
`python3 main.py`. Tkinter is usually included with Python; some Linux
distributions require installing it separately.

## Maze

Choose a marker color and difficulty, then click the marker at the start and
guide it to the goal while holding the left mouse button. After releasing the
button, you can continue from the end of the drawn path.

- **Easy:** the marker can leave the path.
- **Hard:** leaving the path clears the drawing and returns the marker to the start.

The **Restart** button starts a new game. Changing the difficulty also starts a
new game. The **Menu** button returns to the minigame selection screen.

## Android

Build a debug APK in Ubuntu or WSL with the Android SDK license accepted:

```bash
sudo apt update
sudo apt install -y build-essential git zip unzip openjdk-17-jdk python3-venv python3-dev autoconf automake libtool pkg-config zlib1g-dev libncurses-dev cmake libffi-dev libssl-dev libsqlite3-dev libbz2-dev liblzma-dev libltdl-dev ccache patch curl
python3 -m venv ~/minigames-build-venv
source ~/minigames-build-venv/bin/activate
pip install buildozer cython==0.29.37 setuptools wheel
bash android/build_apk.sh
```

The script prints the APK location. The debug APK targets ARM64 devices with
Android 7.0 or later; the first build downloads the Android build tools.

### GitHub releases

Push a tag matching `version` in `android/buildozer.spec` (for example `v0.6`)
to run the Android release workflow. The resulting GitHub Release contains an
AAB, signed when all signing secrets are available and unsigned otherwise. The
workflow does not upload to Google Play.

To sign the AAB, configure all these repository secrets under **Settings >
Secrets and variables > Actions**. If any are missing, the workflow warns and
releases an unsigned AAB, which must be signed before uploading to Google Play.
Invalid signing credentials still fail the build.

| Secret | Value |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | Base64-encoded upload keystore |
| `ANDROID_KEY_ALIAS` | Alias of the upload key |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_PASSWORD` | Key password |

Use the existing upload key if the app is already registered with Google Play.
Otherwise, create a new key outside the repository. The following Windows
example requires a JDK with `keytool` on `PATH`:

```powershell
keytool -genkeypair -v -keystore "C:\path\to\upload-key.jks" -alias upload -keyalg RSA -keysize 2048 -validity 10000
```

The command prompts for passwords and certificate details. To copy the encoded
keystore for the GitHub secret without printing it:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\upload-key.jks")) | Set-Clipboard
```

Paste it into `ANDROID_KEYSTORE_BASE64`, then clear the clipboard. Keep the
keystore and passwords backed up securely outside the repository; do not commit
or share them. Future Play uploads must use the same upload key unless Google
Play resets it. Uploading the AAB also requires a Play Console account and
meeting Google Play's publishing requirements.

After committing and pushing the workflow and app changes, create and push a
new matching tag:

```bash
git tag v0.6
git push origin v0.6
```

Use a new version and tag for each release.

## Extending and Testing

Each game has its own directory in `games`; new games can be added to the menu
in `main.py`. The maze logic is separate from the Tkinter interface.

```powershell
py -m unittest discover
```
