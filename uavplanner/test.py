from .reader import read_txt

poly = read_txt("test.txt")

print(poly)
print(poly.area)
print(list(poly.exterior.coords))