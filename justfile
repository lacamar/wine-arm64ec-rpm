lint:
    #!/bin/sh
    s=$(git diff --cached --name-only --diff-filter=AM -- '*.spec')
    [ -z "$s" ] || rpmlint $s

test:
    #!/bin/sh
    [ "${PRECHECK:-1}" = 0 ] && exit 0
    for s in $(git diff --name-only '@{u}..HEAD' -- '*.spec' 2>/dev/null); do
        [ -f "$s" ] && { tools/precheck "$s" || exit 1; }
    done
