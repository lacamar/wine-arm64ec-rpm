lint:
    #!/bin/sh
    s=$(git diff --cached --name-only --diff-filter=AM -- '*.spec')
    [ -z "$s" ] || rpmlint $s

ci spec="--all":
    ci/run {{ if spec == "--all" { "--all" } else { "--spec " + spec } }}

ci-test:
    ci/test_compare.py

ci-timer:
    systemctl --user link {{ justfile_directory() }}/ci/wine-arm64ec-ci.service {{ justfile_directory() }}/ci/wine-arm64ec-ci.timer
    systemctl --user enable --now wine-arm64ec-ci.timer

test:
    #!/bin/sh
    [ "${PRECHECK:-1}" = 0 ] && exit 0
    for s in $(git diff --name-only '@{u}..HEAD' -- '*.spec' 2>/dev/null); do
        [ -f "$s" ] && { tools/precheck "$s" || exit 1; }
    done
