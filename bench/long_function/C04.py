import collections
import random
import bench.taint as taint


class V:
    def __init__(self, a, b, c, d, e):
        self.count = 0
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.v = [a, b, c, d, e]

    def func1(self):
        self.count += 1
        n = 0
        for i in range(self.a):
            for j in range(self.b):
                for k in range(self.c):
                    n += i * j * k
        return n

    def func2(self):
        self.count += 2
        min_v = min(self.v)
        max_v = max(self.v)
        new_v = []
        if max_v == min_v:
            return self.v
        for v in self.v:
            new_v.append((v - min_v) / (max_v - min_v))
        return new_v

    def func3(self):
        self.count += 3
        avg_v = sum(self.v) / len(self.v)
        variance_v = 0
        for v in self.v:
            variance_v += (v - avg_v) ** 2
        variance_v /= len(self.v)
        standard_deviation_v = variance_v ** 0.5
        new_v = []
        if standard_deviation_v == 0:
            return self.v
        for v in self.v:
            new_v.append((v - avg_v) / standard_deviation_v)
        return new_v

    def func4(self):
        self.count += 4
        height = self.v
        ans = 0
        left, right = 0, len(height) - 1
        leftMax = rightMax = 0
        while left < right:
            leftMax = max(leftMax, height[left])
            rightMax = max(rightMax, height[right])
            if height[left] < height[right]:
                ans += leftMax - height[left]
                left += 1
            else:
                ans += rightMax - height[right]
                right -= 1
        return ans

    def func5(self):
        self.count += 5
        height = self.v
        l, r = 0, len(height) - 1
        ans = 0
        while l < r:
            area = min(height[l], height[r]) * (r - l)
            ans = max(ans, area)
            if height[l] <= height[r]:
                l += 1
            else:
                r -= 1
        return ans

    def func6(self):
        self.count += 6
        k = random.randint(0, len(self.v))
        nums = self.v
        if not nums or k == 0:
            return []
        deque = collections.deque()
        for i in range(k):
            while deque and deque[-1] < nums[i]:
                deque.pop()
            deque.append(nums[i])
        res = [deque[0]]
        for i in range(k, len(nums)):
            if deque[0] == nums[i - k]:
                deque.popleft()
            while deque and deque[-1] < nums[i]:
                deque.pop()
            deque.append(nums[i])
            res.append(deque[0])
        return res

    def func7(self):
        self.count += 7
        nums = self.v
        n = len(nums)
        hash_size = n + 1
        for i in range(n):
            if nums[i] <= 0 or nums[i] >= hash_size:
                nums[i] = 0
        for i in range(n):
            if nums[i] % hash_size != 0:
                pos = (nums[i] % hash_size) - 1
                nums[pos] = (nums[pos] % hash_size) + hash_size
        for i in range(n):
            if nums[i] < hash_size:
                return i + 1
        return hash_size

    def func8(self):
        self.count += 8
        heights = self.v
        res = 0
        n = len(heights)
        for i in range(n):
            left_i = i
            right_i = i
            while left_i >= 0 and heights[left_i] >= heights[i]:
                left_i -= 1
            while right_i < n and heights[right_i] >= heights[i]:
                right_i += 1
            res = max(res, (right_i - left_i - 1) * heights[i])
        return res

    def func9(self):
        self.count += 9
        heights = self.v
        if not heights:
            return 0
        n = len(heights)
        left_i = [0] * n
        right_i = [0] * n
        left_i[0] = -1
        right_i[-1] = n
        for i in range(1, n):
            tmp = i - 1
            while tmp >= 0 and heights[tmp] >= heights[i]:
                tmp = left_i[tmp]
            left_i[i] = tmp
        for i in range(n - 2, -1, -1):
            tmp = i + 1
            while tmp < n and heights[tmp] >= heights[i]:
                tmp = right_i[tmp]
            right_i[i] = tmp
        res = 0
        for i in range(n):
            res = max(res, (right_i[i] - left_i[i] - 1) * heights[i])
        return res

    def func10(self):
        self.count += 10
        nums = self.v
        if not nums:
            return
        res = nums[0]
        pre_max = nums[0]
        pre_min = nums[0]
        for num in nums[1:]:
            cur_max = max(pre_max * num, pre_min * num, num)
            cur_min = min(pre_max * num, pre_min * num, num)
            res = max(res, cur_max)
            pre_max = cur_max
            pre_min = cur_min
        return res

    def run_func(self):
        self.func1()
        self.func2()
        self.func3()
        self.func4()
        self.func5()
        self.func6()
        self.func7()
        self.func8()
        self.func9()
        self.func10()


def bad(a, b, c, d, e):
    source = taint.source()
    v = V(a, b, c, d, e)
    v.run_func()
    if v.count == 55:
        taint.sink(source)


def good(a, b, c, d, e):
    source = taint.source()
    v = V(a, b, c, d, e)
    v.run_func()
    if v.count != 55:
        taint.sink(source)
