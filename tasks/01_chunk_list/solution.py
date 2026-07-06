def chunk_list(lst, n):
    result = []
    for i in range(0, len(lst) // n * n, n):
        result.append(lst[i:i+n])
    return result
