#! /bin/bash

set -e
set -x

PY2=${PY2:-python2.7}
PY3=${PY3:-python3.3}

patobj='"hel\xc3\xb3lo"'
patdict='{"zz":"more","hello":["fp:s5pIIHf32iiVNH_eBGBMXtlXhMa7dI3w9KBrvHZ-v1NRAA"],"world":"yay","./":"test"}'

for py in $PY3 $PY2; do
    $py sc/fp.py # self-test

    fpt="$py fptool.py"
    objt="$py objtool.py"
    $fpt -h
    $fpt -a fp:s5pIIHf32iiVNH_eBGBMXtlXhMa7dI3w9KBrvHZ-v1NRAA
    $fpt -f hex fp::BV7THYJ6CTZRWMMVJFFMPUQ7DWEO4WW6YTJZFKY2H7RTNK456JF3MXY
    $fpt -f long -s 2 fp::AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAA
    $fpt -f dec fp:s5pIIHf32iiVNH_eBGBMXtlXhMa7dI3w9KBrvHZ-v1NRAA
    $fpt -f carray fp:s5pIIHf32iiVNH_eBGBMXtlXhMa7dI3w9KBrvHZ-v1NRAA
    $fpt -f binary ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    $fpt -f compact b39a4820-77f7da28-95347fde-04604c5e-d95784c6-bb748df0-f4a06bbc-767ebf53
    $fpt -c fp:s5pIIHf32iiVNH_eBGBMXtlXhMa7dI3w9KBrvHZ-v1NRAA fp:DX8z4T4U8xsxlUlKx9IfHYjuWt7E05KrGj_jNqud8ku2Xw || true

    $objt -h

    test1() {
        outr=$1
        shift
        $objt "$@" str:hello $outr
        printf 'hello' | $objt "$@" raw:- $outr
        printf 'he\x00ll\xc3\xb3o!\n' | $objt "$@" raw:- $outr
    }
    for outr in fp:compact fp:long fp:hex fp:binary fp:dec raw:- py:- json:- pickle:- utf8:-; do
        test1 "$outr"
        case $outr in
            json*) test1 "$outr" -b ;;
        esac
    done

    test2() {
        datum=$1
        intr=$2
        shift 2
        s1=`printf "$datum" | $objt json:- fp:compact`
        s2=`printf "$datum" | $objt "$@" json:- $intr | $objt $intr fp:compact`
        test "x$s1" = "x$s2"
        echo "$s1"
    }

    test3() {
        datum=$1
        rm -rf tmp1.d tmp2.d
        printf "$datum" | $objt json:- fs:tmp1.d
        $objt fs:tmp1.d fs:tmp2.d
        diff -r tmp1.d tmp2.d
        $objt fs:tmp1.d fp:compact
        $objt fs:tmp2.d fp:compact
    }

    test4() {
        intr=$1
        shift
        s1=`$objt fs:tmp1.d fp:compact`
        s2=`$objt "$@" fs:tmp1.d $intr | $objt $intr fp:compact`
        test "x$s1" = "x$s2"
        echo "$s1"
    }

    test3 "$patobj"  >>fpobj.tmp
    for intr in json:- pickle:- raw:- utf8:-; do
        test2 "$patobj" "$intr" >>fpobj.tmp
        test4 "$intr" >>fpobj.tmp
        case $intr in
            json*)
                test2 "$patobj" "$intr" -b >>fpobj.tmp
                test4 "$intr" -b >>fpobj.tmp
                ;;
        esac
    done

    test3 "$patdict" >>fpdict.tmp
    for intr in json:- pickle:-; do
        test2 "$patdict" "$intr" >>fpdict.tmp
        test4 "$intr" >>fpdict.tmp
        case $intr in
            json*)
                test2 "$patdict" "$intr" -b >>fpdict.tmp
                test4 "$intr" -b >>fpdict.tmp
                ;;
        esac
    done

    rm -rf tmp2.d
    s1=`echo '{"foo":"","bar":""}' | $objt json:- fp:compact`
    echo '{"foo":"","bar":""}' | $objt json:- fs:tmp2.d
    touch tmp2.d/.baz
    s2=`$objt -i '*foo*' fs:tmp2.d fp:compact`
    s3=`$objt -a fs:tmp2.d fp:compact`
    test "$s1" != "$s2"
    test "$s2" != "$s3"
    test "$s1" != "$s3"
done

n=`uniq <fpobj.tmp | wc -l | awk '{print $1}'`
test $n = 1
n=`uniq <fpdict.tmp | wc -l | awk '{print $1}'`
test $n = 1
