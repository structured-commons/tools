#! /bin/bash

set -e
set -x

PY2=${PY2:-python2.7}
PY3=${PY3:-python3.3}

for py in $PY2 $PY3; do
    $py sc/fp.py # self-test
    $py fptool.py -h
    $py fptool.py -a fp:s5pIIHf32iiVNH_eBGBMXtlXhMa7dI3w9KBrvHZ-v1NRAA
    $py fptool.py -f hex fp::BV7THYJ6CTZRWMMVJFFMPUQ7DWEO4WW6YTJZFKY2H7RTNK456JF3MXY
    $py fptool.py -f long -s 2 fp::AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAA
    $py fptool.py -f dec fp:s5pIIHf32iiVNH_eBGBMXtlXhMa7dI3w9KBrvHZ-v1NRAA
    $py fptool.py -f carray fp:s5pIIHf32iiVNH_eBGBMXtlXhMa7dI3w9KBrvHZ-v1NRAA
    $py fptool.py -f binary ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    $py fptool.py -f compact b39a4820-77f7da28-95347fde-04604c5e-d95784c6-bb748df0-f4a06bbc-767ebf53
    $py fptool.py -c fp:s5pIIHf32iiVNH_eBGBMXtlXhMa7dI3w9KBrvHZ-v1NRAA fp:DX8z4T4U8xsxlUlKx9IfHYjuWt7E05KrGj_jNqud8ku2Xw || true

    $py objtool.py -h
    for outr in fp:compact fp:long fp:hex fp:binary fp:dec raw:- py:- json:-; do
        $py objtool.py str:hello $outr
        printf hello | $py objtool.py raw:- $outr
    done

    true >fplist
    for int in py:- json:-; do
        s1=`echo '{"hello":123,"world":"yay"}' | $py objtool.py py:- fp:compact`
        s2=`echo '{"hello":123,"world":"yay"}' | $py objtool.py py:- $int | $py objtool.py $int fp:compact`
        test "x$s1" = "x$s2"
        echo "$s1" >>fplist
    done

    rm -rf tmp1.d tmp2.d
    echo '{"hello":123,"world":"yay"}' | $py objtool.py py:- fs:tmp1.d
    $py objtool.py fs:tmp1.d fs:tmp2.d
    diff -r tmp1.d tmp2.d
    $py objtool.py fs:tmp1.d fp:compact >>fplist

    n=`uniq <fplist | wc -l | awk '{print $1}'`
    test $n = 1
done
