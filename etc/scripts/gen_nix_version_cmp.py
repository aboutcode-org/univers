#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

"""
Regenerate tests/data/schema/nix_version_cmp.json from the Nix reference
implementation. Requires the ``nix-instantiate`` command: every expected
output is the answer of the real ``builtins.compareVersions``, evaluated over
all pairs from a corpus of version strings chosen to exercise every branch of
the comparison.

Run from the repository root:
    python etc/scripts/gen_nix_version_cmp.py
"""

import itertools
import json
import subprocess
from pathlib import Path

CORPUS = [
    ".",
    "-",
    "1",
    "007",
    "1.0",
    "1.0.0",
    "1-0",
    "1.0.1",
    "1.9",
    "1.10",
    "1.1.1k",
    "2.3",
    "2.3.1",
    "2.3a",
    "2.3b",
    "2.3pre",
    "2.3pre1",
    "2.3.pre1",
    "2.3-pre.1",
    "2.3preX",
    "pre",
    "pre1",
    "a",
    "abc",
    "openssl",
    "2147483647",
    "2147483648",
    "9223372036854775808",
    "1.2147483648",
    "1.2147483648.0",
    "0.0.0",
    "10.0.0",
    "1..2",
    "1.-2",
    "1.0rc1",
    "1.0.rc1",
    "unstable-2024-01-01",
    "0-unstable-2024-01-01",
    "v1.0",
    "V2",
    "ABC",
    "152.0.7977.60",
    "152.0.7977.82",
    "9.8p1",
    "3.0.2-r10",
]

EXPR = (
    "{pairs}: map"
    " (p: builtins.compareVersions (builtins.elemAt p 0) (builtins.elemAt p 1))"
    " (builtins.fromJSON pairs)"
)

OUTPUT = Path(__file__).parent.parent.parent / "tests" / "data" / "schema" / "nix_version_cmp.json"


def main():
    pairs = list(itertools.product(CORPUS, repeat=2))
    out = subprocess.run(
        [
            "nix-instantiate",
            "--eval",
            "--strict",
            "--json",
            "--expr",
            EXPR,
            "--argstr",
            "pairs",
            json.dumps(pairs),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    results = json.loads(out)

    entries = []
    for (version1, version2), result in zip(pairs, results):
        if result == 0:
            entries.append(
                {
                    "description": "Equality test for Nix version, "
                    "generated from builtins.compareVersions.",
                    "test_group": "basic",
                    "test_type": "equality",
                    "input": {"input_scheme": "nix", "versions": [version1, version2]},
                    "expected_output": True,
                }
            )
        else:
            ordered = [version1, version2] if result < 0 else [version2, version1]
            entries.append(
                {
                    "description": "Comparison test for Nix version, "
                    "generated from builtins.compareVersions.",
                    "test_group": "basic",
                    "test_type": "comparison",
                    "input": {"input_scheme": "nix", "versions": [version1, version2]},
                    "expected_output": ordered,
                }
            )

    with open(OUTPUT, "w") as f:
        json.dump(entries, f, indent=1)
    print(f"wrote {len(entries)} entries to {OUTPUT}")


if __name__ == "__main__":
    main()
