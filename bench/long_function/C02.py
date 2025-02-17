import collections
import itertools
from typing import List
import bench.taint as taint


def f(args):
    if args.a < 0:
        args.a = -args.a
        f(args)
    elif args.a > 100:
        return
    else:
        args.a *= 2
        i_list = []
        if args.b < 0:
            num = 0
            for i in range(-args.b):
                i_list.append(i)
                num += i
                if num > args.a:
                    break
            if num > args.a:
                args.b = num
            else:
                args.b = args.a - num
        elif args.b == 0:
            for i in range(args.a):
                args.b += i
        elif args.b >= args.a:
            args.b = args.b % args.a
        else:
            for i in range(args.a - 1, 0, -1):
                if args.a % i == 0:
                    args.b = i
                    break
        args.b = Solution().treeOfInfiniteSouls(i_list, 100000007, args.b)
        f(args)


class Solution:
    def __init__(self):
        self.MOD = None

    def treeOfInfiniteSouls(self, a: List[int], p: int, r: int) -> int:
        self.MOD = p
        n = len(a)
        lnum = n // 2
        rnum = n - lnum
        ways = self.sea(n)
        res = 0
        for way in ways:
            tmp, tidx = (0, 0)
            for idx, i in enumerate(way):
                if i == '}':
                    tmp += 1
                if tmp == lnum:
                    tidx = idx
                    break
            ls, rs = (way[:tidx + 1], way[tidx + 1:])
            for xlist in itertools.combinations(a, lnum):
                xcount = collections.Counter(xlist)
                ylist = []
                ylen = len(rs) - rnum * 2
                for i in a:
                    if xcount[i] > 0:
                        xcount[i] -= 1
                    else:
                        ylen += len(str(i))
                        ylist.append(i)
                xtmp = pow(10, ylen, self.MOD)
                xdict = collections.defaultdict(int)
                for new_xlist in itertools.permutations(xlist, lnum):
                    xmod = self.get_val(ls, new_xlist)
                    xval = xmod * xtmp % self.MOD
                    xdict[xval] += 1
                for new_ylist in itertools.permutations(ylist, rnum):
                    ymod = self.get_val(rs, new_ylist)
                    yval = (r - ymod) % self.MOD
                    res += xdict[yval]
        return res

    def sea(self, n):
        if n == 1:
            return ['1{}9']
        res = []
        for i in range(1, n):
            llist, rlist = (self.sea(i), self.sea(n - i))
            for l in llist:
                for r in rlist:
                    res.append(f'1{l}{r}9')
        return res

    def get_val(self, s, vlist):
        val = s.format(*vlist)
        return int(val) % self.MOD


def bad(args):
    source = taint.source()
    args.a = 1
    f(args)
    if args.a == 128:
        taint.sink(source)


def good(args):
    source = taint.source()
    args.a = 1
    f(args)
    if args.a != 128:
        taint.sink(source)
