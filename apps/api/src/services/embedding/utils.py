def batch(values: list[str], size: int) -> list[list[str]]:
  if size <= 0:
    return [values]
  return [values[index:index + size] for index in range(0, len(values), size)]
