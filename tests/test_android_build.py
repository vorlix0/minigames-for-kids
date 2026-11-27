import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SIGNING_VARS = (
    "P4A_RELEASE_KEYSTORE",
    "P4A_RELEASE_KEYALIAS",
    "P4A_RELEASE_KEYSTORE_PASSWD",
    "P4A_RELEASE_KEYALIAS_PASSWD",
)


class AndroidBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        stub = self.root / "buildozer"
        stub.write_text(
            "#!/usr/bin/env bash\n"
            "set -eu\n"
            'printf "%s\\n" "$*" >> "$CALLS"\n'
            'env | grep "^P4A_RELEASE_" > "$SIGNING_ENV" || true\n'
            "mkdir -p bin\n"
            'if [[ "$2" == release ]]; then touch bin/app.aab; '
            'else touch bin/app.apk; fi\n'
        )
        stub.chmod(0o755)
        self.env = os.environ.copy()
        for name in SIGNING_VARS:
            self.env.pop(name, None)
        self.env.update(
            HOME=str(self.root),
            PATH=f"{self.root}{os.pathsep}{self.env['PATH']}",
            CALLS=str(self.root / "calls"),
            SIGNING_ENV=str(self.root / "signing-env"),
            AAB_OUTPUT_DIR=str(self.root / "output"),
            BUILD_DEBUG_APK="0",
            BUILD_RELEASE_AAB="1",
        )

    def run_build(self):
        return subprocess.run(
            ["bash", str(ROOT / "android/build_apk.sh")],
            env=self.env, text=True, capture_output=True,
        )

    def test_unsigned_release_unsets_empty_signing_variables(self):
        self.env.update({name: "" for name in SIGNING_VARS})
        result = self.run_build()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "calls").read_text(), "android release\n")
        self.assertEqual((self.root / "signing-env").read_text(), "")
        self.assertTrue((self.root / "output/app.aab").exists())

    def test_signed_release_passes_credentials(self):
        keystore = self.root / "key"
        keystore.touch()
        self.env.update(dict(zip(SIGNING_VARS, (str(keystore), "alias", "store", "key"))))
        result = self.run_build()
        self.assertEqual(result.returncode, 0, result.stderr)
        signing_env = (self.root / "signing-env").read_text()
        for name in SIGNING_VARS:
            self.assertIn(f"{name}={self.env[name]}\n", signing_env)
        self.assertEqual((self.root / "calls").read_text(), "android release\n")
        self.assertTrue((self.root / "output/app.aab").exists())

    def test_partial_signing_configuration_fails(self):
        self.env["P4A_RELEASE_KEYALIAS"] = "alias"
        result = self.run_build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing required signing variable", result.stderr)
        self.assertFalse((self.root / "calls").exists())


if __name__ == "__main__":
    unittest.main()
